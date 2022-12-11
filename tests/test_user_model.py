import pytest
from unittest.mock import patch
from datetime import datetime
from flask import Flask
import string
import random

from app import db
from app.models import User, Transaction, Category, Bank


def test_password_hashing() -> None:
    user_1 = User(password="password_1")
    assert user_1.check_password("password_1")
    assert not user_1.check_password("wrong_password")
    with pytest.raises(AttributeError):
        user_1.password


def test_reset_password_tokens(app: Flask, user_1: User) -> None:
    token = user_1.get_reset_password_token()
    assert user_1.verify_reset_password_token(token) == user_1

    new = random.choices(string.ascii_letters, k=5)
    token = token.replace(token[:5], "".join(new))
    assert user_1.verify_reset_password_token(token) == None


def test_user_update(app: Flask, user_1: User, transaction_1: Transaction) -> None:

    user_1.update(dict(first_name="first_2", username="username_2"))
    assert user_1.first_name == "first_2"
    assert user_1.username == "username_2"

    with patch("app.models.Transaction.convert_to_main_amount") as convert_mock:
        # Convert_to_main_amount is only called if user is updated with new currency
        user_1.update(dict(main_currency="USD"))
        assert convert_mock.call_count == 0
        user_1.update(dict(main_currency="EUR"))
        assert convert_mock.call_count == 1


def test_user_selects(app: Flask, user_1: User) -> None:
    user_2 = User(
        username="username_2",
        password="password_2",
        email="email_2@gmail.com",
        first_name="first_2",
        last_name="last_2",
        main_currency="USD",
    )
    bank_1 = Bank(name="Revolut", statement_type="csv")
    bank_2 = Bank(name="mBank", statement_type="xml")
    bank_3 = Bank(name="Equabank", statement_type="xml")
    category_1 = Category(name="Groceries", user=user_1)
    category_2 = Category(name="Car", user=user_1)
    category_3 = Category(name="Restaurants", user=user_2)

    with patch("app.models.Transaction.convert_to_main_amount"):
        transaction_1 = Transaction(
            info="info_1",
            title="title_1",
            main_amount=1,
            base_amount=11,
            base_currency="CZK",
            transaction_date=datetime(2001, 1, 1, 1, 1, 1, 1),
            creation_date=datetime(2011, 1, 1, 1, 1, 1, 1),
            place="place_1",
            user=user_1,
        )
        transaction_2 = Transaction(
            info="info_2",
            title="title_2",
            main_amount=2,
            base_amount=22,
            base_currency="EUR",
            transaction_date=datetime(2002, 2, 2, 2, 2, 2, 2),
            creation_date=datetime(2022, 2, 2, 2, 2, 2, 2),
            place="place_2",
            user=user_1,
            category=category_1,
            bank=bank_1,
        )
        transaction_3 = Transaction(
            info="info_3",
            title="title_3",
            main_amount=3,
            base_amount=33,
            base_currency="USD",
            transaction_date=datetime(2003, 3, 3, 3, 3, 3, 3),
            creation_date=datetime(2033, 3, 3, 3, 3, 3, 3),
            place="place_3",
            user=user_1,
            category=category_2,
            bank=bank_2,
        )

        transaction_4 = Transaction(
            info="info_4",
            title="title_4",
            main_amount=4,
            base_amount=44,
            base_currency="EUR",
            transaction_date=datetime(2004, 4, 4, 4, 4, 4, 4),
            creation_date=datetime(2044, 4, 4, 4, 4, 4, 4),
            place="place_4",
            user=user_2,
            category=category_2,
            bank=bank_2,
        )

    assert user_1.select_banks() == [bank_1, bank_2]
    assert user_1.select_base_currencies() == ["CZK", "EUR", "USD"]
    assert user_1.select_categories() == [category_1, category_2]
    assert user_1.select_transactions() == [
        transaction_1,
        transaction_2,
        transaction_3,
    ]
