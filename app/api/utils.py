from flask import current_app
from flask_login import current_user
from flask_sqlalchemy import BaseQuery
import requests
from requests.exceptions import RequestException
from collections import defaultdict
import typing as t

from app import cache
from app.models import Transaction
from app.exceptions import InvalidConfigError
from app import logger

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


def convert_currency(
    transactions: list[Transaction], user_currency: str
) -> list[Transaction]:
    """Convert all main_amounts in transactions to the currency set by user.

    Args:
        transactions (list[Transaction]): list of transactions to convert
        user_currency (str): the currency set by user

    Raises:
        InvalidConfigError: raised in case API key is not attached to apps config file

    Returns:
        list[Transaction]: list of converted transactions
    """

    base_url = (
        "https://api.currencyscoop.com/v1/historical?api_key={key}&base={user_currency}"
    )
    date_template = "&date={date}"

    if "CURRENCYSCOOP_API_KEY" in current_app.config:
        base_url = base_url.format(
            key=current_app.config["CURRENCYSCOOP_API_KEY"], user_currency=user_currency
        )
    else:
        raise InvalidConfigError("CurrencyScoop API key is not accessible")

    # date_cache = {
    #   "EUR": {
    #       "10-11-2021": {
    #           "USD": 0.95,
    #       },
    #   },
    # }
    date_cache: dict[str, dict[str, list]] = cache.get(
        "conversion_rates"
    ) or defaultdict(dict)

    API_counter = 0
    for transaction in transactions:
        # Check if conversion is necessary
        if transaction.base_currency == user_currency:
            transaction.main_amount = transaction.base_amount
            logger.log(
                "DEBUG_HIGH",
                f"{transaction.base_amount} {transaction.base_currency} -> {transaction.main_amount} {user_currency}",
            )
            continue

        # Stringified transaction date used for
        date = transaction.transaction_date.strftime("%Y-%m-%d")

        # Check if currency exchange rates are already cached for this date
        # If not, consume API and populate the date_cache with it
        if not date_cache or date not in date_cache[user_currency]:
            date_param = date_template.format(date=date)

            try:
                r = requests.get(base_url + date_param)
                r.raise_for_status()
            except RequestException as error:
                logger.error("Error during currency conversion: ", error)

            json = r.json()["response"]
            base_currency, rates = json["base"], json["rates"]
            date_cache[base_currency][date] = rates
            API_counter += 1

        # Calculate the amount
        transaction.main_amount = round(
            transaction.base_amount
            / date_cache[user_currency][date][transaction.base_currency],
            2,
        )
        logger.log(
            "DEBUG_HIGH",
            f"{transaction.base_amount} {transaction.base_currency} -> {transaction.main_amount} {user_currency}",
        )

    cache.set("conversion_rates", date_cache)
    logger.debug(
        f"API was consumed {API_counter} times for {len(transactions)} transactions"
    )
    return transactions


@cache.cached(key_prefix="available_currencies")
def get_currencies() -> list[str]:
    """Consume CurrencyScoop API to get currency codes available for currency conversion

    Raises:
        InvalidConfigError: Invalid flask config for CurrencyScoop

    Returns:
        list[str]: list of available currency codes
    """

    base_url = "https://api.currencyscoop.com/v1/currencies?api_key={key}&type=fiat"

    if "CURRENCYSCOOP_API_KEY" in current_app.config:
        base_url = base_url.format(key=current_app.config["CURRENCYSCOOP_API_KEY"])
    else:
        raise InvalidConfigError("CurrencyScoop API key is not accessible")

    try:
        r = requests.get(base_url)
        r.raise_for_status()
    except RequestException as error:
        print("Error during currency load: ", error)

    response = r.json()
    currencies = list(response["response"]["fiats"].keys())

    return currencies
