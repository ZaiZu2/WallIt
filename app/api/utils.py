import typing as t
from pathlib import Path

from app import db
from app.exceptions import InvalidConfigError
from app.models import Bank


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
