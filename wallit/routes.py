#! python3

from click import FileError
from sqlalchemy import select
from wallit import app, db, logger
from wallit.forms import LoginForm, SignUpForm, ResetPasswordForm
from wallit.models import Transaction, User, Bank, Category
from wallit.imports import (
    import_equabank_statement,
    import_revolut_statement,
    validate_statement,
    convert_currency,
)

from flask import redirect, url_for, render_template, flash, request, abort
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from datetime import datetime
from typing import Callable


@app.route("/")
@login_required
def index():

    return render_template(
        "index.html", current_user=current_user._get_current_object()
    )


@app.route("/welcome", methods=["GET"])
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    login_form = LoginForm()
    sign_up_form = SignUpForm()
    reset_password_form = ResetPasswordForm()

    return render_template(
        "welcome.html",
        login_form=login_form,
        sign_up_form=sign_up_form,
        reset_password_form=reset_password_form,
    )


@app.route("/login", methods=["POST"])
def login():
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).one()
        if user is None or not user.check_password(login_form.password.data):
            flash("Invalid username or password", "login_message")
            return redirect(url_for("welcome"))

        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for("index"))

    # Reassing form.errors to flash as they will be inaccessible after after redirection
    for field in login_form._fields.values():
        for error in field.errors:
            flash(error, "login_message")
    return redirect(url_for("welcome"))


@app.route("/account/reset", methods=["POST"])
def reset_password():
    reset_password_form = ResetPasswordForm()
    if reset_password_form.validate_on_submit():
        if User.query.filter_by(email=reset_password_form.email.data).one():
            # send email with password reset form
            flash("Email with password reset form was sent", "reset_password_message")
            return redirect(url_for("welcome"))

        flash("Account with given email does not exist", "reset_password_message")

    # Reassign form.errors to flash as they will be inaccessible after after redirection
    for field in reset_password_form._fields.values():
        for error in field.errors:
            flash(error, "reset_password_message")
    return redirect(url_for("welcome"))


@app.route("/account/new", methods=["POST"])
def sign_up():
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        if User.query.filter_by(username=sign_up_form.username.data).one():
            flash("Username is already used, 'sign_up_message'")
            return redirect(url_for("welcome"))
        if User.query.filter_by(email=sign_up_form.email.data).one():
            flash("Email is already used", "sign_up_message")
            return redirect(url_for("welcome"))

        new_user = User(
            username=sign_up_form.username.data,
            email=sign_up_form.email.data,
            password=sign_up_form.password.data,
            first_name=sign_up_form.first_name.data,
            last_name=sign_up_form.last_name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully", "sign_up_message")
        return redirect(url_for("welcome"))

    # Reassign form.errors to flash as they will be inaccessible after after redirection
    for field in sign_up_form._fields.values():
        for error in field.errors:
            flash(error, "sign_up_message")
    return redirect(url_for("welcome"))


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/api/transactions/fetch", methods=["POST"])
@login_required
def post_transactions():
    """Receive filter parameters in JSON, query DB for filtered values
    and return Transactions serialized to JSON

    Request JSON structure example:
    {
        'amount': {'max': '123123', 'min': '213'},
        'date': {'max': '2022-07-21', 'min': '2022-07-07'}
        'base_currency': ['CZK', 'USD'],
        'bank': ['mBank', 'Revolut'],
        'category': ['Salary', 'Hobby', 'Restaurant'],
    }

    Response JSON structure example:
    {
        "transactions": [
        {
            "amount": 61800.05,
            "bank": "mBank",
            "base_amount": 3193.0,
            "base_currency": "USD",
            "category": "groceries",
            "date": "Mon, 08 Feb 2021 15:02:58 GMT",
            "info": null,
            "place": "Bengubelan",
            "title": null
        },
        ...,
        ]
    }

    Returns:
        dict: JSON with transaction data
    """

    # Dictionary mapping queried values to the keys used for serialization and request processing
    # Request JSON filter names must remain the same as the keys used here
    TABLE_MAP = {
        "info": Transaction.info,
        "title": Transaction.title,
        "amount": Transaction.main_amount,
        "base_amount": Transaction.base_amount,
        "base_currency": Transaction.base_currency,
        "date": Transaction.transaction_date,
        "place": Transaction.place,
        "category": Category.name,
        "bank": Bank.name,
    }

    filters = request.json

    query = (
        select([column for column in TABLE_MAP.values()])
        .filter_by(user_id=current_user.id)
        .select_from(Transaction)
        .join(Category, isouter=True)  # left outer join
        .join(Bank, isouter=True)  # left outer join
    )

    # iterate over dict of filters
    for filter_name, filter_values in filters.items():
        # check if filter is a range (dict), then read 'min' and 'max' values if they were given
        if isinstance(filter_values, dict):
            if filter_values["min"]:
                query = query.filter(TABLE_MAP[filter_name] >= filter_values["min"])
            if filter_values["max"]:
                query = query.filter(TABLE_MAP[filter_name] <= filter_values["max"])

        # check if filter holds checkbox values (list), then read contained values if there are any
        if isinstance(filter_values, list):
            if filter_values:
                query = query.filter(TABLE_MAP[filter_name].in_(filter_values))

    results = db.session.execute(query).all()
    logger.debug(query.compile(compile_kwargs={"literal_binds": True}).string)

    # Serializing data received from the DB
    table_rows = []
    for row in results:
        result_dict = {}
        for column_name, column_value in zip(TABLE_MAP.keys(), row):
            # serialize date to ISO 8601 string format
            if isinstance(column_value, datetime):
                result_dict[column_name] = column_value.isoformat()
            else:
                result_dict[column_name] = column_value

        table_rows.append(result_dict)

    return {"transactions": table_rows}


@app.route("/api/transactions/filters", methods=["GET"])
@login_required
def fetch_filters() -> dict:
    """Fetch dynamic filtering values for user

    Response JSON structure example:
    {
        "bank": [
            "Equabank",
            "mBank",
            "Revolut"
        ],
        "base_currency": [
            "EUR",
            "CZK",
            "USD"
        ],
        "category": [
            "groceries",
            "restaurant",
            "salary"
        ]
    }

    Returns:
        dict: lists containing values for each filtering parameter
    """

    # Dict with prespecified filtering categories, to be filled with queried values
    filter_dict = {
        "base_currency": "",
        "category": "",
        "bank": "",
    }

    category_query = select(Category.name.distinct()).filter_by(user_id=current_user.id)
    filter_dict["category"] = db.session.scalars(category_query).all()

    bank_query = (
        select(Bank.name.distinct())
        .select_from(Transaction)
        .join(Bank)
        .filter(Transaction.user_id == current_user.id)
    )
    filter_dict["bank"] = db.session.scalars(bank_query).all()

    currency_query = select(Transaction.base_currency.distinct()).filter(
        Transaction.user_id == current_user.id
    )
    filter_dict["base_currency"] = db.session.scalars(currency_query).all()

    return filter_dict


@app.route("/api/transactions/upload", methods=["POST"])
@login_required
def upload_statements():

    # TODO: Needed check for duplicate Transactions
    # both in files being loaded, and in the DB

    # Maps request parameters to corresponding banks
    BANK_MAP = {
        "revolut": {
            "import_func": import_revolut_statement,
            "instance": Bank.query.filter_by(name="Revolut").one(),
        },
        "equabank": {
            "import_func": import_equabank_statement,
            "instance": Bank.query.filter_by(name="Equabank").one(),
        },
    }
    # dictionary holding filenames which failed to upload
    failed_upload: dict[str, str] = {}
    # dictionary holding filenames which were successfully uploaded
    success_upload: dict[str, str] = {}
    # list holding all imported transactions
    uploaded_transactions: list[Transaction] = []

    for statement_origin, file in request.files.items(True):
        # Sanitize the filename
        filename = secure_filename(file.filename)

        # Check if user attached file to a form
        if filename:
            if validate_statement(statement_origin, filename, file.stream):
                # Run import function corresponding to statement_origin
                import_function: Callable = BANK_MAP[statement_origin]["import_func"]

                try:
                    temp_transactions: list[Transaction] = import_function(
                        file, current_user, BANK_MAP[statement_origin]["instance"]
                    )
                except FileError as e:
                    failed_upload[statement_origin] = filename

                # Append transactions from all files to the main list
                uploaded_transactions.extend(temp_transactions)
                success_upload[statement_origin] = filename
            else:
                failed_upload[statement_origin] = filename

    uploaded_transactions = convert_currency(
        uploaded_transactions, current_user.main_currency
    )
    db.session.add_all(uploaded_transactions)
    db.session.commit()

    # If only some files were uploaded, report partial success
    if len(failed_upload) > 0 and len(success_upload) > 0:
        return {"failed": failed_upload, "success": success_upload}, 206
    if len(success_upload) == 0:
        abort(400)
    if len(failed_upload) == 0:
        return "", 201
