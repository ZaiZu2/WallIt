from wallit import db, logger
from wallit.models import Bank, Category, Transaction

from flask_login import current_user
from flask_sqlalchemy import BaseQuery

import typing as t

JSONType = str | int | float | bool | None | t.Dict[str, t.Any] | t.List[t.Any]


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
