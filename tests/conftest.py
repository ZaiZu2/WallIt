import pytest
from unittest.mock import patch
from flask import Flask
from flask.testing import FlaskClient
from flask_login import login_user
from typing import Generator
from datetime import datetime

from app import create_app, db
from app.models import User, Transaction, Category
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "postgresql://test:test@localhost:5434/wallit_test"
    SECRET_KEY = "test"
    WTF_CSRF_ENABLED = False


@pytest.fixture()
def app() -> Generator[Flask, None, None]:
    app = create_app(TestConfig)

    app_context = app.app_context()
    app_context.push()
    test_context = app.test_request_context()
    test_context.push()
    db.create_all()
    yield app
    db.session.close()
    db.drop_all()
    test_context.pop()
    app_context.pop()


@pytest.fixture()
def client(app: Flask) -> FlaskClient:
    return app.test_client()


@pytest.fixture()
def user_1(app: Flask) -> User:
    user_1 = User(
        username="username1",
        password="password1",
        email="email1@gmail.com",
        first_name="firstOne",
        last_name="lastOne",
        main_currency="USD",
    )
    db.session.add(user_1)
    db.session.commit()
    return user_1


@pytest.fixture()
def logged_user_1(user_1: User) -> User:
    login_user(user_1, remember=True)
    return user_1


@pytest.fixture()
def user_2(app: Flask) -> User:
    user_2 = User(
        username="username2",
        password="password2",
        email="email2@gmail.com",
        first_name="firstTwo",
        last_name="lastTwo",
        main_currency="EUR",
    )
    db.session.add(user_2)
    db.session.commit()
    return user_2


@pytest.fixture()
def logged_user_2(user_2: User) -> User:
    login_user(user_2, remember=True)
    return user_2


@pytest.fixture()
def category_1(user_1: User) -> Category:
    category_1 = Category(
        name="name1",
        user=user_1,
    )
    db.session.add(category_1)
    db.session.commit()
    return category_1


@pytest.fixture()
def category_2(user_2: User) -> Category:
    category_2 = Category(
        name="name2",
        user=user_2,
    )
    db.session.add(category_2)
    db.session.commit()
    return category_2


@pytest.fixture()
def transaction_1(user_1: User, category_1: Category) -> Transaction:
    with patch("app.models.Transaction.convert_to_main_amount"):
        transaction_1 = Transaction(
            info="info1",
            title="title1",
            main_amount=1,
            base_amount=11,
            base_currency="CZK",
            transaction_date=datetime(2001, 1, 1, 1, 1, 1, 1),
            creation_date=datetime(2011, 1, 1, 1, 1, 1, 1),
            place="place1",
            user=user_1,
            category=category_1,
        )
    db.session.add(transaction_1)
    db.session.commit()
    return transaction_1


@pytest.fixture()
def transaction_2(user_2: User, category_2: Category) -> Transaction:
    with patch("app.models.Transaction.convert_to_main_amount"):
        transaction_2 = Transaction(
            info="info2",
            title="title2",
            main_amount=2,
            base_amount=22,
            base_currency="CZK",
            transaction_date=datetime(2002, 2, 2, 2, 2, 2, 2),
            creation_date=datetime(2022, 2, 2, 2, 2, 2, 2),
            place="place2",
            user=user_2,
            category=category_2,
        )
    db.session.add(transaction_2)
    db.session.commit()
    return transaction_2
