import flask_sqlalchemy
import sqlalchemy
from wallit import db, logger
from wallit.models import Bank, Category, Transaction
from wallit.schemas import TransactionFilterSchema

from flask_login import current_user
from flask_sqlalchemy import BaseQuery

from datetime import datetime

def filter_transactions(filters: dict) -> list[Transaction]:
    # Dictionary mapping queried values to the keys used for serialization and request processing
    # Request JSON filter names must remain the same as the keys used here

    FILTER_MAP = {
        "amount" : Transaction.base_amount,
        "date" : Transaction.transaction_date,
        "base_currencies" : Transaction.base_currency,
        "banks" : Transaction.bank,
        "categories" : Transaction.category
    }

    query: BaseQuery = Transaction.query.filter_by(user=current_user)
    # iterate over dict of filters
    for filter_name, filter_values in filters.items():
        # check if filter is a range (dict), then read 'min' and 'max' values if they were given
        if isinstance(filter_values, dict):
            if filter_values["min"] is not None:
                query = query.filter(FILTER_MAP[filter_name] >= filter_values["min"])
            if filter_values["max"] is not None:
                query = query.filter(FILTER_MAP[filter_name] <= filter_values["max"])

        # check if filter holds checkbox values (list), then read contained values if there are any
        if isinstance(filter_values, list):
            if filter_values is not None:
                query = query.filter(FILTER_MAP[filter_name].in_(filter_values))
    
    transactions: list[Transaction] = query.all()
    logger.debug(str(query))
    # logger.debug(query.compile(compile_kwargs={"literal_binds": True}).string)

    return transactions