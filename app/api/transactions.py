from flask import request, abort
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
from sqlalchemy import select, func, between, and_, case
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
from typing import Callable

from app import db, logger
from app.models import Transaction, User, Bank
from app.api import blueprint
from app.api.schemas import (
    TransactionSchema,
    ModifyTransactionSchema,
    FiltersSchema,
    MonthlySaldoSchema,
)
from app.api.imports import (
    import_equabank_statement,
    import_revolut_statement,
)
from app.api.utils import (
    filter_transactions,
    validate_statement,
)
from app.exceptions import FileError


@blueprint.route("/api/transactions", methods=["POST"])
@login_required
def fetch_transactions() -> ResponseReturnValue:
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
    return TransactionSchema(many=True).dump(transactions), 201


@blueprint.route("/api/transactions/add", methods=["POST"])
@login_required
def add_transaction() -> ResponseReturnValue:
    """Add transaction"""

    verified_data = TransactionSchema().load(request.json)
    transaction = Transaction(user=current_user, **verified_data)
    db.session.add(transaction)
    db.session.commit()

    return TransactionSchema().dump(transaction), 201


@blueprint.route("/api/transactions/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_transaction(id: int) -> tuple[str, int]:
    "Modify 'info','title','place', 'category' column of the transaction"

    if not (transaction := Transaction.get_from_id(id, current_user)):
        abort(404)
    verified_data = ModifyTransactionSchema().load(request.json)
    transaction.update(verified_data)
    db.session.commit()
    return TransactionSchema().dump(transaction), 200


@blueprint.route("/api/transactions/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_transaction(id: int) -> tuple[dict, int]:
    """Delete transaction with given Id"""

    if not (transaction := Transaction.get_from_id(id, current_user)):
        abort(404)
    db.session.delete(transaction)
    db.session.commit()
    return {}, 200


@blueprint.route("/api/users/<int:id>/delete_transactions", methods=["DELETE"])
@login_required
def delete_all_transactions(id: int) -> ResponseReturnValue:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    no_of_deleted = Transaction.query.filter_by(user=user).delete()
    db.session.commit()
    return {"number_of_deleted": no_of_deleted}, 200


@blueprint.route("/api/transactions/upload", methods=["POST"])
@login_required
def upload_statements() -> ResponseReturnValue:
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


@blueprint.route("/api/transactions/monthly", methods=["GET"])
@login_required
def monthly_statements() -> ResponseReturnValue:
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
        ResponseReturnValue: (response, http_code)
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

    return MonthlySaldoSchema(many=True).dump(saldo), 200
