from unittest.mock import patch
from datetime import datetime

from app.models import User, Transaction


def test_transaction_creation(user_1: User) -> None:
    """Check if currency conversion is called for every newly created Transaction"""

    with patch("app.models.Transaction.convert_to_main_amount") as convert_mock:
        transaction_1 = Transaction(
            main_amount=11,
            base_amount=1,
            base_currency="CZK",
            transaction_date=datetime(2001, 1, 1, 1, 1, 1, 1),
            user=user_1,
        )
        assert convert_mock.call_count == 1


def test_transaction_update(transaction_1: Transaction) -> None:
    """Check if currency conversion is called for every Transaction,
    which is updated with base_currency or base_amount"""

    with patch("app.models.Transaction.convert_to_main_amount") as convert_mock:
        transaction_1.update(
            dict(
                info="info_2",
                title="title_2",
                transaction_date=datetime(2002, 2, 2, 2, 2, 2, 2),
            )
        )
        assert transaction_1.info == "info_2"
        assert transaction_1.title == "title_2"
        assert transaction_1.transaction_date == datetime(2002, 2, 2, 2, 2, 2, 2)
        assert convert_mock.call_count == 0

        # Convert_to_main_amount is only called if user is updated with new currency
        transaction_1.update(dict(base_currency="USD"))
        assert convert_mock.call_count == 1
        transaction_1.update(dict(base_amount=22))
        assert convert_mock.call_count == 2


def test_get_from_id(
    user_1: User,
    user_2: User,
    transaction_1: Transaction,
    transaction_2: Transaction,
) -> None:
    assert Transaction.get_from_id(transaction_1.id, user_1) == transaction_1
    assert Transaction.get_from_id(transaction_2.id, user_2) == transaction_2
    assert Transaction.get_from_id(transaction_1.id, user_2) == None
    assert Transaction.get_from_id(transaction_2.id, user_1) == None
