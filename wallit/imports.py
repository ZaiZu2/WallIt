#!python3

from email.mime import base
from email.policy import default
from re import I
from wallit import app, db, cache
from wallit.models import Transaction, User, Bank
from wallit.exceptions import FileError, InvalidConfigError
from wallit import logger

from pathlib import Path
from typing import Dict
import typing
import io
import csv
from datetime import datetime
import xml.etree.ElementTree as ET
import requests
from requests.exceptions import RequestException
from collections import defaultdict


def validate_statement(origin: str, filename: str, file: typing.IO[bytes]) -> bool:
    """Validate the uploaded file for correct extension and content (to be implemented)

    Args:
        origin (str): bank origin of statement
        filename (str): sanitized filename
        file (typing.BinaryIO): file binary stream for content validation

    Returns:
        bool: True if successfully validated
    """
    # TODO: Additional file content validation

    is_validated = False

    # Query for acceptable statement extensions associated with each bank
    results = db.session.query(Bank.name, Bank.statement_type)
    extension_map: Dict[str, str] = {
        bank_name.lower(): file_extension for (bank_name, file_extension) in results
    }

    try:
        # Check correctness of the associated filetype
        if Path(filename).suffix == extension_map[origin]:
            is_validated = True
            return is_validated
    except KeyError:
        raise InvalidConfigError

    return is_validated


def import_revolut_statement(
    file: typing.BinaryIO, user: User, bank: Bank
) -> list[Transaction]:
    """Load Transactions from Revolut monthly bank statement in .csv file format

    Args:
        file (typing.BinaryIO): binary stream from which data is parsed

    Raises:
        FileError: raised in case of any errors during file processing

    Returns:
        list[Transaction]: list of parsed transactions
    """

    transactions: list[Transaction] = []

    with io.TextIOWrapper(file, encoding="utf-8") as csv_file:
        try:
            reader = csv.DictReader(csv_file, delimiter=",")

            for row in reader:
                # Ignore rows with internal revolut exchanges
                if row["Type"] != "EXCHANGE":
                    transaction = Transaction()

                    transaction.info = row["Type"]
                    transaction.title = row["Description"]
                    transaction.base_amount = float(row["Amount"])
                    transaction.base_currency = row["Currency"]
                    transaction.transaction_date = datetime.strptime(
                        row["Completed Date"], "%Y-%m-%d %H:%M:%S"
                    )
                    transaction.bank_id = bank.id
                    transaction.user_id = user.id

                    transactions.append(transaction)
        except Exception as e:
            raise FileError("Error during parsing necessary statement details") from e

    return transactions


def import_equabank_statement(
    file: typing.BinaryIO, user: User, bank: Bank
) -> list[Transaction]:
    """Load Transactions from Equabank monthly bank statement in .xml file format

    Args:
        file (typing.BinaryIO): _description_

    Raises:
        FileError: raised in case of any errors during file processing

    Returns:
        list[Transaction]: list of Transactions which were loaded
    """

    # TODO: Handling multiple transactions which are not unique by DB standards (UNIQUE amount, currency, date)
    # Due to incomplete/generalized transaction date in Equabank XML,
    # it's not possible to clearly define transaction uniqueness
    # Solution1: providing additional column in DB which indexes transactions
    # having same (amount, currency, date) combo?
    # Solution2: requirement from the user to manually modify date or other UNIQUEness
    # parameter during XML loading process
    # TODO: Wierd sum calculation method.

    def parse_record(root_obj: ET.Element, XPath: str) -> str | None:
        """Parse record string from XML Ntry element - can be None"""

        found_element = root_obj.find(XPath, namespace)
        if isinstance(found_element, ET.Element) and isinstance(
            found_element.text, str
        ):
            return found_element.text.upper()
        else:
            return None

    def parse_amount(
        root_obj: ET.Element, amount_XPath: str, vector_XPath: str
    ) -> tuple[float, str]:
        """Parse tuple (Amount, Currency) from transaction element"""

        # Parsing element containing amount/currency
        amount_element = root_obj.find(amount_XPath, namespace)
        # Parsing value specifying incoming/outgoing payment
        vector = parse_record(root_obj, vector_XPath)

        if isinstance(amount_element, ET.Element):
            amount = amount_element.text
            currency = amount_element.get("Ccy")
        else:
            raise FileError(
                "Error during parsing necessary statement details - amount/currency"
            )

        if (
            isinstance(amount, str)
            and isinstance(currency, str)
            and isinstance(vector, str)
        ):
            if vector == "DBIT":
                return (-1 * float(amount), currency)
            else:
                return (float(amount), currency)
        else:
            raise FileError(
                "Error during parsing necessary statement details - amount/currency"
            )

    def parse_date(root_obj: ET.Element, XPath: str) -> datetime:
        """Parse date string from transaction element"""

        date_element = root_obj.find(XPath, namespace)
        if isinstance(date_element, ET.Element) and isinstance(date_element.text, str):
            return datetime.strptime(date_element.text, "%Y-%m-%d+%H:%M")
        else:
            raise FileError("Error during parsing necessary statement details - date")

    def validate_sum(
        root_obj: ET.Element, sum_XPath: str, vector_XPath: str, calculated_sum: float
    ) -> bool:
        """Check if sum of parsed transaction expenses is the same
        as the sum stated in the statement"""

        statement_sum = parse_record(root_obj, sum_XPath)
        vector = parse_record(root, vector_XPath)

        if isinstance(statement_sum, str) and isinstance(vector, str):
            if vector == "CRDT":
                statement_float_sum = -1 * float(statement_sum)
            else:
                statement_float_sum = float(statement_sum)
        else:
            raise FileError(
                "Error during parsing necessary statement details - transaction sum"
            )

        if round(calculated_sum, 2) == statement_float_sum:
            return True
        else:
            return False

    # temp list holding loaded Transactions
    transactions: list[Transaction] = []

    with io.TextIOWrapper(file, encoding="utf-8") as xml_file:
        # Variable holding calculated sum of all parsed expenses from a single file
        calculated_sum = 0.0

        try:
            tree = ET.parse(xml_file)
            root = tree.getroot()
            namespace = {"nms": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.06"}

            # iterate through transaction elements in the statement tree
            for transaction_element in root.findall(".//nms:Ntry", namespace):

                # Parsing transaction data
                transaction = Transaction()
                transaction.info = parse_record(
                    transaction_element, ".//nms:RltdPties//nms:Nm"
                )
                transaction.title = parse_record(transaction_element, ".//nms:Ustrd")
                transaction.place = parse_record(
                    transaction_element, ".//nms:PstlAdr/nms:TwnNm"
                )
                transaction.transaction_date = parse_date(
                    transaction_element, ".//nms:BookgDt/nms:Dt"
                )
                transaction.base_amount, transaction.base_currency = parse_amount(
                    transaction_element,
                    amount_XPath="./nms:Amt",
                    vector_XPath="./nms:CdtDbtInd",
                )
                transaction.bank_id = bank.id
                transaction.user_id = user.id

                transactions.append(transaction)
                calculated_sum += transaction.base_amount
        except (ET.ParseError) as e:
            raise FileError("Error during parsing statement - general failure") from e

        if not validate_sum(
            root_obj=root,
            sum_XPath=".//nms:TtlNtries/nms:TtlNetNtry/nms:Amt",
            vector_XPath=".//nms:TtlNtries/nms:TtlNetNtry/nms:CdtDbtInd",
            calculated_sum=calculated_sum,
        ):
            raise FileError("Error during parsing statement - validation failed")

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

    if "CURRENCYSCOOP_API_KEY" in app.config:
        base_url = base_url.format(
            key=app.config["CURRENCYSCOOP_API_KEY"], user_currency=user_currency
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

    if "CURRENCYSCOOP_API_KEY" in app.config:
        base_url = base_url.format(key=app.config["CURRENCYSCOOP_API_KEY"])
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
