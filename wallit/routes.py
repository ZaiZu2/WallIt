from marshmallow import ValidationError
from wallit import app, db, logger
from wallit.forms import LoginForm, RequestPasswordForm, SignUpForm, ResetPasswordForm
from wallit.models import Transaction, User, Bank, Category
from wallit.schemas import (
    CategorySchema,
    ChangePasswordSchema,
    ModifyUserSchema,
    SessionEntitiesSchema,
    TransactionSchema,
    ModifyTransactionSchema,
    UserEntitiesSchema,
    FiltersSchema,
    UserSchema,
    MonthlySaldoSchema,
)
from wallit.imports import (
    import_equabank_statement,
    import_revolut_statement,
    validate_statement,
    convert_currency,
    get_currencies,
)
from wallit.helpers import filter_transactions, send_password_reset_email, JSONType
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
from collections import defaultdict


@app.route("/index")
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
    request_password_form = RequestPasswordForm()

    return render_template(
        "menus.html",
        login_form=login_form,
        sign_up_form=sign_up_form,
        request_password_form=request_password_form,
    )


@app.route("/login", methods=["POST"])
def login() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
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


@app.route("/logout", methods=["GET"])
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/reset_password", methods=["POST"])
def request_reset_password() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    request_password_form = RequestPasswordForm()
    if request_password_form.validate_on_submit():
        if user := User.query.filter_by(email=request_password_form.email.data).first():
            send_password_reset_email(user)
        flash("Email with password reset form was sent", "reset_password_message")
        return redirect(url_for("welcome"))

    # Reassign form.errors to flash as they will be inaccessible after redirection
    for field in request_password_form._fields.values():
        for error in field.errors:
            flash(error, "reset_password_message")
    return redirect(url_for("welcome"))


@app.route("/reset_password/<string:token>", methods=["GET", "POST"])
def reset_password(token: str) -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for("welcome"))
    reset_password_form = ResetPasswordForm()
    if reset_password_form.validate_on_submit():
        user.set_password(reset_password_form.password.data)
        db.session.commit()
        flash("Password has been successfully reset", "login_message")
        return redirect(url_for("welcome"))
    return render_template(
        "reset_password.html", reset_password_form=reset_password_form
    )


@app.route("/users/new", methods=["POST"])
def sign_up() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for("index"))
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


@app.route("/api/users/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_user(id: int) -> Tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    try:
        verified_data = ModifyUserSchema().load(request.json)
    except ValidationError as error:
        return error.messages, 400

    if (
        "main_currency" in verified_data
        and verified_data["main_currency"] != user.main_currency
    ):
        convert_currency(user.select_transactions(), verified_data["main_currency"])

    user.update(verified_data)
    db.session.commit()

    return UserSchema().dumps(user), 200


@app.route("/api/users/<int:id>/change_password", methods=["PATCH"])
@login_required
def change_password(id: int) -> Tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    try:
        verified_data = ChangePasswordSchema().load(request.json)
    except ValidationError as error:
        return error.messages, 400

    if not user.check_password(verified_data["old_password"]):
        abort(400)
    user.set_password(verified_data["new_password"])
    db.session.commit()

    return {}, 200


@app.route("/api/users/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_user(id: int) -> Tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    db.session.delete(user)
    # db.session.commit()
    return {}, 200


@app.route("/api/users/<int:id>/delete_transactions", methods=["DELETE"])
@login_required
def delete_all_transactions(id: int) -> Tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    no_of_deleted = Transaction.query.filter_by(user=user).delete()
    db.session.commit()
    return {"number_of_deleted": no_of_deleted}, 200


@app.route("/api/transactions", methods=["POST"])
@login_required
def fetch_transactions() -> Tuple[JSONType, int]:
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

    transaction_filters = FiltersSchema().load(request.json)
    transactions = filter_transactions(transaction_filters)
    return TransactionSchema(many=True).dumps(transactions), 201


@app.route("/api/transactions/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_transaction(id: int) -> Tuple[str, int]:
    """Delete transaction with given Id"""

    transaction = Transaction.get_from_id(id, current_user)
    db.session.delete(transaction)
    db.session.commit()
    return {}, 200


@app.route("/api/transactions/add", methods=["POST"])
@login_required
def add_transaction() -> Tuple[JSONType, int]:
    """Add transaction"""

    verified_data = TransactionSchema().load(request.json)
    transaction = Transaction(user=current_user, **verified_data)
    transaction = convert_currency([transaction], current_user.main_currency)[0]
    db.session.add(transaction)
    db.session.commit()

    return TransactionSchema().dumps(transaction), 201


@app.route("/api/transactions/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_transaction(id: int) -> Tuple[str, int]:
    "Modify 'info','title','place', 'category' column of the transaction"

    transaction = Transaction.get_from_id(id, current_user)
    verified_data = ModifyTransactionSchema().load(request.json)
    transaction.update(verified_data)
    db.session.commit()
    return TransactionSchema().dumps(transaction), 200


@app.route("/api/categories/add", methods=["POST"])
@login_required
def add_category() -> tuple[JSONType, int]:
    """Add category"""

    verified_data = CategorySchema().load(request.json)
    category = Category(user=current_user, **verified_data)
    db.session.add(category)
    db.session.commit()
    return CategorySchema().dumps(category), 201


@app.route("/api/categories/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_category(id: int) -> tuple[JSONType, int]:
    """Modify category"""

    verified_data = CategorySchema().load(request.json)
    category = Category.get_from_id(id, current_user)
    category.update(verified_data)
    db.session.commit()
    return CategorySchema().dumps(category), 201


@app.route("/api/categories/delete", methods=["DELETE"])
@login_required
def delete_category() -> tuple[JSONType, int]:
    """Delete multiple categories"""

    verified_data = CategorySchema(many=True).load(request.json, partial=True)

    deleted_categories = []
    for category in verified_data:
        if category := Category.get_from_id(category["id"], current_user):
            deleted_categories.append(category)

    for deleted_category in deleted_categories:
        db.session.delete(deleted_category)
    db.session.commit()

    return CategorySchema(many=True).dumps(deleted_categories), 201


@app.route("/api/entities", methods=["GET"])
@login_required
def fetch_session_entities() -> tuple[JSONType, int]:
    """Get basic session data required for front-end function

    Response JSON structure example:
    {
        "currencies": ["USD", "EUR", ...],
        "banks": {
            "Revolut": {"id":1,"name":"Revolut"},
            "Equabank":{"id":2,"name":"Equabank"},
            ...
        }
    }

    Returns:
        tuple[JSONType, int]: _description_
    """
    response_body: dict[str, list | dict] = defaultdict(dict)
    response_body["currencies"] = get_currencies()
    for bank in Bank.query.all():
        response_body["banks"][bank.name] = bank

    return SessionEntitiesSchema().dumps(response_body), 200


@app.route("/api/user/entities", methods=["GET"])
@login_required
def fetch_user_entities() -> tuple[JSONType, int]:
    """Fetch entities assigned to user

    Response JSON structure example:
    {
        "bank": ["Equabank", "Revolut", ...],
        "base_currency": ["EUR", "CZK", "USD", ...],
        "category": ["groceries", "restaurant", "salary", ...],
        "currency_codes": ["USD", "EUR", "CZK", ...]
    }

    Returns:
        dict: lists containing values for each filtering parameter
    """

    response_body: dict[str, list | dict] = defaultdict(dict)

    response_body["user_details"] = current_user
    response_body["base_currencies"] = current_user.select_base_currencies()
    for category in current_user.select_categories():
        response_body["categories"][category.name] = category
    for bank in current_user.select_banks():
        response_body["banks"][bank.name] = bank

    # Schema used only to map server-side 'json' names to general ones specified by schema
    return UserEntitiesSchema().dumps(response_body), 200


@app.route("/api/transactions/upload", methods=["POST"])
@login_required
def upload_statements() -> tuple[JSONType, int]:
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


@app.route("/api/transactions/monthly", methods=["GET"])
@login_required
def monthly_statements() -> tuple[JSONType, int]:
    """Return list of monthly saldos featuring incoming, outgoing and balance value

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

    oldest = (
        Transaction.query.with_entities(func.min(Transaction.transaction_date))
        .filter_by(user=current_user)
        .scalar()
    )
    # No transactions related to the user
    if not oldest:
        return {}, 404

    oldest = oldest - relativedelta(day=1, hour=0, minute=0, second=0)
    newest = (
        Transaction.query.with_entities(func.max(Transaction.transaction_date))
        .filter_by(user=current_user)
        .scalar()
    )

    # Only create monthly summary for months which has ended
    # Do not query for the current month
    if newest.year == datetime.now().year and newest.month == datetime.now().month:
        newest = newest - relativedelta(months=+1, day=1, hour=0, minute=0, second=0)
    else:
        newest = newest - relativedelta(day=1, hour=0, minute=0, second=0)

    incoming = func.sum(
        case((Transaction.main_amount > 0, Transaction.main_amount), else_=0)
    )
    outgoing = func.sum(
        case((Transaction.main_amount < 0, Transaction.main_amount), else_=0)
    )
    # list containing monthly statements
    saldo = []
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
        logger.log(
            "DEBUG_HIGH", query.compile(compile_kwargs={"literal_binds": True}).string
        )

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
