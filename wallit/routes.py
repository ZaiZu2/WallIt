#! python3

from sqlalchemy import select
from wallit import app, db, logger
from wallit.forms import LoginForm, SignUpForm, ResetPasswordForm
from wallit.models import Transaction, User, Bank, Category
from wallit.schemas import (
    TransactionFilterSchema,
    TransactionSchema,
    MonthlySaldoSchema,
)
from wallit.imports import (
    import_equabank_statement,
    import_revolut_statement,
    validate_statement,
    convert_currency,
)
from wallit.helpers import filter_transactions, JSONType
from wallit.exceptions import FileError

from flask import redirect, url_for, render_template, flash, request, abort
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename
from werkzeug.wrappers import Response

from sqlalchemy import select, func, between, and_, case
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from typing import Any, Callable, Tuple


@app.route("/")
@login_required
def index() -> str:

    return render_template(
        "index.html", current_user=current_user._get_current_object()
    )


@app.route("/welcome", methods=["GET"])
def welcome() -> str | Response:
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
def login() -> Response:
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
def reset_password() -> Response:
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
def sign_up() -> Response:
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        if User.query.filter_by(username=sign_up_form.username.data).first():
            flash("Username is already used, 'sign_up_message'")
            return redirect(url_for("welcome"))
        if User.query.filter_by(email=sign_up_form.email.data).first():
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

    # Reassign form.errors to flash as they will be inaccessible after redirection
    for field in sign_up_form._fields.values():
        for error in field.errors:
            flash(error, "sign_up_message")
    return redirect(url_for("welcome"))


@app.route("/logout", methods=["GET"])
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/api/transactions/fetch", methods=["POST"])
@login_required
def post_transactions() -> JSONType:
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

    transaction_filters = TransactionFilterSchema().load(request.json)
    transactions = filter_transactions(transaction_filters)
    return TransactionSchema(many=True).dumps(transactions), 201


@app.route("/api/transactions/filters", methods=["GET"])
@login_required
def fetch_filters() -> JSONType:
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
        "base_currencies": "",
        "categories": "",
        "banks": "",
    }

    category_query = select(Category.name.distinct()).filter_by(user=current_user)
    filter_dict["categories"] = db.session.scalars(category_query).all()

    bank_query = (
        select(Bank.name.distinct())
        .select_from(Transaction)
        .join(Bank)
        .filter(Transaction.user == current_user)
    )
    filter_dict["banks"] = db.session.scalars(bank_query).all()

    currency_query = select(Transaction.base_currency.distinct()).filter(
        Transaction.user == current_user
    )
    filter_dict["base_currencies"] = db.session.scalars(currency_query).all()

    # Schema used only to map server-side 'json' names to general ones specified by schema
    schema = TransactionFilterSchema(only=("banks", "base_currencies", "categories"))
    return schema.dumps(filter_dict)


@app.route("/api/transactions/upload", methods=["POST"])
@login_required
def upload_statements() -> JSONType:
    """Parse and save transactions from uploaded files

    Response JSON structure example:
    {
        'amount': 34,
        'info': '',
        'failed': {
            '1029848317_20191231_2019005.xml': 'revolut',
            '1029848317_20210131_2021001.xml': 'revolut'
        }
        'success': {'1029848317_20210131_2021001.xml': 'equabank'}
    }

    Returns:
        dict: response containing data about upload outcome
    """

    # TODO: Needed check for duplicate Transactions
    # both in files being loaded, and in the DB

    # Check if user uploaded any statements
    is_empty = True
    for file in request.files.values():
        if file.filename:
            is_empty = False
    if is_empty:
        return {"info": "No files were uploaded."}, 400

    # Maps request parameters to corresponding banks
    BANK_MAP = {
        "revolut": {
            "import_func": import_revolut_statement,
            "instance": Bank.query.filter_by(name="Revolut").one(),
            "aaa": Bank.get_from_name("Revolut"),
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
                except FileError:
                    failed_upload[filename] = statement_origin

                # Append transactions from all files to the main list
                uploaded_transactions.extend(temp_transactions)
                success_upload[filename] = statement_origin
            else:
                failed_upload[filename] = statement_origin

    uploaded_transactions = convert_currency(
        uploaded_transactions, current_user.main_currency
    )
    db.session.add_all(uploaded_transactions)
    db.session.commit()

    upload_results = {
        "failed": failed_upload,
        "success": success_upload,
        "amount": len(uploaded_transactions),
        "info": "",
    }

    if failed_upload and success_upload:
        return upload_results, 206
    if not success_upload:
        return upload_results, 415
    if not failed_upload:
        return upload_results, 201


@app.route("/api/transactions/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_transaction(id: int) -> Tuple[str, int]:
    """Delete transaction with given Id"""

    transaction = Transaction.get_from_id(id, current_user)
    db.session.delete(transaction)
    db.session.commit()
    return "", 200


@app.route("/api/transactions/add", methods=["POST"])
@login_required
def add_transaction() -> Tuple[dict[str, int], int]:
    """Add transaction"""

    transactionSchema = TransactionSchema()
    transaction = transactionSchema.load(request.json)
    db.session.add(transaction)
    db.session.commit()
    # Successful deletion, returning new ID of the transaction for client-side synchronization
    return {"id": transaction.id}, 200


@app.route("/api/transactions/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_transaction(id: int) -> Tuple[str, int]:
    "Modify 'info','title','place' column of the transaction"

    transaction = Transaction.get_from_id(id, current_user)
    schema = TransactionSchema(only=("info", "title", "place", "category"))
    transaction = schema.load(request.json, instance=transaction)
    db.session.commit()
    return "", 204


@app.route("/api/transactions/monthly", methods=["GET"])
def monthly_statements() -> tuple[JSONType, int]:
    """Return list of monthly saldos featuring incoming, outgoing and balance

    Response JSON structure example:
    [
        {
            balance: 32207.87
            incoming: 79464.5
            month: "2019-10"
            outgoing: -47256.63
        }, ...
    ]

    Returns:
        tuple[JSONType, int]: (response, http_code)
    """

    # list containing monthly statements
    saldo = []

    oldest = (
        Transaction.query.with_entities(func.min(Transaction.transaction_date))
        .filter_by(user=current_user)
        .scalar()
    )
    oldest = oldest - relativedelta(day=1, hour=0, minute=0, second=0)
    newest = (
        Transaction.query.with_entities(func.max(Transaction.transaction_date))
        .filter_by(user=current_user)
        .scalar()
    )
    newest = newest - relativedelta(months=+1, day=1, hour=0, minute=0, second=0)

    # Main query for monthly saldos
    incoming = func.sum(
        case((Transaction.main_amount > 0, Transaction.main_amount), else_=0)
    )
    outgoing = func.sum(
        case((Transaction.main_amount < 0, Transaction.main_amount), else_=0)
    )
    # Iterate over time period, querying for incoming/outgoing sums
    for month in rrule(freq=MONTHLY, dtstart=oldest, until=newest):
        query = select(incoming, outgoing).where(
            and_(
                between(
                    Transaction.transaction_date,
                    month,
                    month + relativedelta(months=+1),
                ),
                Transaction.user == current_user,
            )
        )

        results = db.session.execute(query).all()[0]
        logger.debug(query.compile(compile_kwargs={"literal_binds": True}).string)

        if results[0]:
            saldo.append(
                {
                    "month": month,
                    "outgoing": round(results[1], 2),
                    "incoming": round(results[0], 2),
                    "balance": round(results[0] + results[1], 2),
                }
            )

    return MonthlySaldoSchema(many=True).dumps(saldo), 200
