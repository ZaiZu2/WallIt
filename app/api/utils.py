import typing as t
from pathlib import Path

from app import db
from app.exceptions import InvalidConfigError
from app.models import Bank, MyBanks


def validate_statement(origin: MyBanks, filename: str, file: t.IO[bytes]) -> bool:
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
    correct = db.session.query(Bank.statement_type).filter_by(name_enum=origin).scalar()

    try:
        # Check correctness of the associated filetype
        if Path(filename).suffix[1:] == correct:
            is_validated = True
            return is_validated
    except KeyError:
        raise InvalidConfigError

    return is_validated
