import typing as t
from pathlib import Path

from flask_login import current_user
from flask_sqlalchemy import BaseQuery

from app import db, logger
from app.exceptions import InvalidConfigError
from app.models import Bank, Transaction


def filter_transactions(filters: dict) -> list[Transaction]:
    # Dictionary mapping queried values to the keys used for serialization and request processing
    # Request JSON filter names must remain the same as the keys used here

    FILTER_MAP = {
        "amount": Transaction.base_amount,
        "date": Transaction.transaction_date,
        "base_currencies": Transaction.base_currency,
        "banks": Transaction.bank_id,
        "categories": Transaction.category_id,
    }

    query: BaseQuery = Transaction.query.filter_by(user=current_user)
    # iterate over dict of filters
    for filter_name, filter_values in filters.items():
        # check if filter is a range (dict), then read 'min' and 'max' values if they were given
        if filter_name in ["amount", "date"]:
            if filter_values["min"] is not None:
                query = query.filter(FILTER_MAP[filter_name] >= filter_values["min"])
            if filter_values["max"] is not None:
                query = query.filter(FILTER_MAP[filter_name] <= filter_values["max"])

        if filter_name == "base_currencies" and filter_values is not None:
            query = query.filter(FILTER_MAP[filter_name].in_(filter_values))

        if filter_name in ["categories", "banks"] and filter_values is not None:
            query = query.filter(FILTER_MAP[filter_name].in_(filter_values))

    query = query.order_by(Transaction.transaction_date.desc())

    transactions: list[Transaction] = query.all()
    logger.debug(str(query))
    # logger.debug(query.compile(compile_kwargs={"literal_binds": True}).string)

    return transactions


def validate_statement(origin: str, filename: str, file: t.IO[bytes]) -> bool:
    """Validate the uploaded file for correct extension and content

    Args:
        origin (str): bank origin of statement
        filename (str): sanitized filename
        file (t.BinaryIO): file binary stream for content validation

    Returns:
        bool: True if successfully validated
    """
    # TODO: Additional file content validation

    is_validated = False

    # Query for acceptable statement extensions associated with each bank
    results = db.session.query(Bank.name, Bank.statement_type).all()
    extension_map: dict[str, str] = {
        bank_name.lower(): file_extension for (bank_name, file_extension) in results
    }

    try:
        # Check correctness of the associated filetype
        if Path(filename).suffix[1:] == extension_map[origin]:
            is_validated = True
            return is_validated
    except KeyError:
        raise InvalidConfigError

    return is_validated
