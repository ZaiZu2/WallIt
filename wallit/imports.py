#!python3

from wallit.models import Transaction, User, Bank
from wallit.exceptions import FileError

from pathlib import Path
import typing
import io
import csv
from datetime import datetime
import xml.etree.ElementTree as ET


def validate_statement(origin: str, filename: str, file: typing.BinaryIO) -> bool:
    """Validate the uploaded file for correct extension and content (to be implemented)

    Args:
        origin (str): bank origin of statement
        filename (str): sanitized filename
        file (typing.BinaryIO): file binary stream for content validation

    Returns:
        bool: True if successfully validated
    """
    # TODO: Additional file content validation
    # TODO: Later on it can be queried from DB
    statement_extensions = {"revolut": ".csv", "equabank": ".xml"}
    # Flag denoting if validation was successful
    is_validated = False

    # Check origin of statement and correct type of the associated file
    for bank, extension in statement_extensions.items():
        if origin == bank and Path(filename).suffix == extension:
            is_validated = True
            return is_validated

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
                transaction = Transaction()

                transaction.base_amount = row["Amount"]
                transaction.base_currency = row["Currency"]
                transaction.transaction_date = datetime.strptime(
                    row["Completed Date"], "%Y-%m-%d %H:%M:%S"
                ).isoformat()
                transaction.title = row["Description"]
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
        root_obj: ET.Element, amount_XPath: str, vector_XPath
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

    def parse_date(root_obj: ET.Element, XPath: str) -> str:
        """Parse date string from transaction element"""

        date_element = root_obj.find(XPath, namespace)
        if isinstance(date_element, ET.Element) and isinstance(date_element.text, str):
            return datetime.strptime(date_element.text, "%Y-%m-%d+%H:%M").isoformat()
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

            # iterate through <Ntry> nodes in the statement tree
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
            raise FileError(f"Wrong .xml file structure. Import aborted.") from e

        if not validate_sum(
            root_obj=root,
            sum_XPath=".//nms:TtlNtries/nms:TtlNetNtry/nms:Amt",
            vector_XPath=".//nms:TtlNtries/nms:TtlNetNtry/nms:CdtDbtInd",
            calculated_sum=calculated_sum,
        ):
            raise FileError("Error during parsing statement - validation failed")

    return transactions
