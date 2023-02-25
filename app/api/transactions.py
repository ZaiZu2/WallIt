from copy import deepcopy
from datetime import datetime
from typing import Callable

from dateutil.relativedelta import relativedelta
from dateutil.rrule import MONTHLY, rrule
from flask import abort, request
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy import and_, between, case, func, select
from werkzeug.utils import secure_filename

from app import db, logger
from app.api import blueprint
from app.api.imports import BANK_IMPORT_MAP
from app.api.schemas import (
    FiltersSchema,
    ModifyTransactionSchema,
    MonthlySaldoSchema,
    TransactionSchema,
)
from app.api.utils import validate_statement
from app.exceptions import FileError
from app.models import Bank, MyBanks, Transaction, User


@blueprint.route("/api/transactions", methods=["GET"])
@login_required
def fetch_transactions() -> ResponseReturnValue:
    """Filter for transactions based on url-encoded filtering parameters

    Request JSON structure example:
    {
        'amount_min': '213',
        'amount_max': '393',
        'date_min': '2022-07-07',
        'date_min': '2022-12-07',
        'base_currency': ['CZK', 'USD'],
        'bank': ['mBank', 'Revolut'],
        'category': ['Salary', 'Hobby', 'Restaurant'],
    }

    Returns:
        dict: list of transactions
    """

    filters = FiltersSchema().load(dict(request.args))

    FILTER_MAP = {
        "amount_min": Transaction.base_amount,
        "amount_max": Transaction.base_amount,
        "date_min": Transaction.transaction_date,
        "date_max": Transaction.transaction_date,
        "base_currencies": Transaction.base_currency,
        "banks": Transaction.bank_id,
        "categories": Transaction.category_id,
    }

    query = Transaction.query.filter_by(user=current_user)

    for filter_name, filter_values in filters.items():
        if filter_name in ("amount_min", "date_min"):
            query = query.filter(FILTER_MAP[filter_name] >= filter_values)
        if filter_name in ("amount_max", "date_max"):
            query = query.filter(FILTER_MAP[filter_name] <= filter_values)
        if filter_name in ("base_currencies", "categories", "banks"):
            query = query.filter(FILTER_MAP[filter_name].in_(filter_values))

    query = query.order_by(Transaction.transaction_date.desc())
    transactions: list[Transaction] = query.all()
    logger.debug(str(query))
    # logger.log("DEBUG_HIGH", query.compile(compile_kwargs={"literal_binds": True}).string)

    return TransactionSchema(many=True).dump(transactions), 200


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
        abort(404, "Transaction not found")
    verified_data = ModifyTransactionSchema().load(request.json)
    transaction.update(verified_data)
    db.session.commit()
    return TransactionSchema().dump(transaction), 200


@blueprint.route("/api/transactions/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_transaction(id: int) -> tuple[dict, int]:
    """Delete transaction with given Id"""

    if not (transaction := Transaction.get_from_id(id, current_user)):
        abort(404, "Transaction not found")
    db.session.delete(transaction)
    db.session.commit()
    return {}, 200


@blueprint.route("/api/users/<int:id>/delete_transactions", methods=["DELETE"])
@login_required
def delete_all_transactions(id: int) -> ResponseReturnValue:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404, "User not found")

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
    file_included = any([file.filename for file in request.files.values()])
    if not file_included:
        return {"info": "No files were provided."}, 400

    # dictionary holding filenames which failed to upload
    failed_upload: dict[str, str] = {}
    # dictionary holding filenames which were successfully uploaded
    success_upload: dict[str, str] = {}
    # list holding all imported transactions
    uploaded_transactions: list[Transaction] = []

    for i, (bank_name, file) in enumerate(request.files.items(True)):
        # Sanitize the filename
        filename = secure_filename(file.filename)
        filename = f"sanitized_filename_{i}" if not filename else filename

        if validate_statement(MyBanks(bank_name), filename, file.stream):
            # Run import function corresponding to bank_name
            import_function: Callable = BANK_IMPORT_MAP[MyBanks(bank_name)]

            try:
                temp_transactions = import_function(file, current_user)
            except FileError:
                failed_upload[filename] = "Errors while parsing the file"

            # Append transactions from all files to the main list
            uploaded_transactions.extend(temp_transactions)
            success_upload[filename] = bank_name
        else:
            failed_upload[filename] = "Corrupted file type or contents"

    db.session.add_all(uploaded_transactions)
    db.session.commit()

    upload_results = {
        "failed": failed_upload,
        "success": success_upload,
        "amount": len(uploaded_transactions),
        "info": "",
    }

    if not failed_upload:
        return upload_results, 201
    if not success_upload:
        return upload_results, 415
    else:
        return upload_results, 206


@blueprint.route("/api/users/<int:id>/monthly", methods=["GET"])
@login_required
def monthly_statements(id: int) -> ResponseReturnValue:
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
    user: User = User.query.get(id)
    if user != current_user:
        abort(404, "User not found")

    oldest = (
        Transaction.query.with_entities(func.min(Transaction.transaction_date))
        .filter_by(user=current_user)
        .scalar()
    )
    # No transactions related to the user
    if not oldest:
        abort(404, "User has no transactions to build summary from")

    oldest = oldest - relativedelta(day=1, hour=0, minute=0, second=0)
    newest = (
        Transaction.query.with_entities(func.max(Transaction.transaction_date))
        .filter_by(user=user)
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
                Transaction.user == user,
            )
        )

        results = db.session.execute(query).all()[0]
        # logger.log(
        #     "DEBUG_HIGH", query.compile(compile_kwargs={"literal_binds": True}).string
        # )

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
