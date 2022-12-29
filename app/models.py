from __future__ import annotations

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin
from flask import current_app
from sqlalchemy import UniqueConstraint, CheckConstraint, select, Table, Column, Integer, Float
from sqlalchemy.orm import with_parent, mapper
from datetime import datetime
import jwt
from time import time
import requests
from requests.exceptions import RequestException
from collections import defaultdict

from app import db, login, cache
from app.exceptions import InvalidConfigError, ExternalError


class UpdatableMixin:
    def update(self, data: dict) -> None:
        for column, value in data.items():
            setattr(self, column, value)


class User(UserMixin, UpdatableMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    main_currency = db.Column(db.String(3), default="CZK", nullable=False)

    transactions = db.relationship(
        "Transaction",
        cascade="all, delete",
        passive_deletes=True,
        back_populates="user",
        lazy=True,
        uselist=True,
    )
    categories = db.relationship(
        "Category",
        cascade="all, delete",
        passive_deletes=True,
        back_populates="user",
        lazy=True,
        uselist=True,
    )

    def __init__(self, username: str, email: str, password: str, **kwargs) -> None:
        super(User, self).__init__(username=username, email=email, **kwargs)
        self.set_password(password)

    def __repr__(self) -> str:
        return f"{self.username}: {self.first_name} {self.last_name} under email: {self.email}"

    def update(self, data: dict) -> None:
        if "main_currency" in data and data["main_currency"] != self.main_currency:
            for transaction in self.select_transactions():
                transaction.convert_to_main_amount(data["main_currency"])
        super(self.__class__, self).update(data)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self) -> str:
        """Generate token used for authentication password reset form

        Returns:
            str: generated token
        """
        return jwt.encode(
            {
                "email": self.email,
                "exp": time() + current_app.config["RESET_TOKEN_MINUTES"] * 60,
            },
            current_app.config["SECRET_KEY"],
            "HS256",
        )

    @staticmethod
    def verify_reset_password_token(token: str) -> User | None:
        """Verify token used for authentication password reset form

        Args:
            token (str): Token to be verified

        Returns:
            User | None: User model object if token was authenticated successfully
        """
        try:
            email = jwt.decode(token, current_app.config["SECRET_KEY"], ["HS256"])[
                "email"
            ]
        except:
            return None
        return User.query.filter_by(email=email).first()

    def select_transactions(self) -> list[Transaction]:
        return Transaction.query.where(with_parent(self, User.transactions)).all()

    def select_categories(self) -> list[Category]:
        return Category.query.where(with_parent(self, User.categories)).all()

    def select_banks(self) -> list[Bank]:
        return (
            Bank.query.select_from(Transaction)
            .join(Bank)
            .filter(Transaction.user == self)
            .distinct()
            .all()
        )

    def select_base_currencies(self) -> list[str]:
        return db.session.scalars(
            select(Transaction.base_currency)
            .where(with_parent(self, User.transactions))
            .distinct()
        ).all()


@login.user_loader
def load_user(id: str) -> User:
    return User.query.get(int(id))


class Transaction(UpdatableMixin, db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.Text, index=True)
    title = db.Column(db.Text)
    main_amount = db.Column("main_amount", db.Float, index=True, nullable=False)
    base_amount = db.Column(db.Float, index=True, nullable=False)
    base_currency = db.Column(db.String(3), index=True, nullable=False)
    transaction_date = db.Column(db.DateTime, index=True, nullable=False)
    creation_date = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.utcnow
    )
    place = db.Column(db.Text)

    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bank_id = db.Column(db.Integer, db.ForeignKey("banks.id"))

    category = db.relationship("Category", back_populates="transactions")
    user = db.relationship("User", back_populates="transactions")
    bank = db.relationship("Bank", back_populates="transactions")

    def __init__(
        self,
        base_amount: float,
        base_currency: str,
        transaction_date: datetime,
        **kwargs,
    ) -> None:
        super(Transaction, self).__init__(
            base_amount=base_amount,
            base_currency=base_currency,
            transaction_date=transaction_date,
            **kwargs,
        )
        self.convert_to_main_amount(self.user.main_currency)

    def __repr__(self) -> str:
        return f"Transaction: {self.base_amount} {self.base_currency} on {self.transaction_date}"

    def update(self, data: dict) -> None:
        super(self.__class__, self).update(data)
        if "base_amount" in data or "base_currency" in data:
            self.convert_to_main_amount()

    def convert_to_main_amount(self, target_currency: str | None = None) -> None:
        """Calculate the transaction value from base currency to user's currency

        Raises:
            InvalidConfigError: raised due to error during API key read
        """
        if target_currency is None:
            target_currency = self.user.main_currency
        if target_currency == self.base_currency:
            self.main_amount = self.base_amount
            return

        # date_cache = {
        #   "EUR": {
        #       "10-11-2021": {
        #           "USD": 0.95, ...
        #       },
        #   },
        # }
        date_cache: dict[str, dict[str, dict[str, int]]] = cache.get(
            "conversion_rates"
        ) or defaultdict(dict)
        # Check if currency exchange rates are already cached for this date
        # If not, consume API and populate the date_cache with it
        date = self.transaction_date.strftime("%Y-%m-%d")
        if not date_cache or date not in date_cache[target_currency]:
            if set(["CURRENCYSCOOP_API_KEY", "CURRENCYSCOOP_API_URL"]).issubset(
                current_app.config
            ):
                api_url = current_app.config["CURRENCYSCOOP_API_URL"].format(
                    key=current_app.config["CURRENCYSCOOP_API_KEY"],
                    target_currency=target_currency,
                    date=date,
                )
            else:
                raise InvalidConfigError("CurrencyScoop API key is not accessible")

            try:
                r = requests.get(api_url)
                r.raise_for_status()
                json = r.json()["response"]
            except RequestException as error:
                raise ExternalError(error)

            base_currency, rates = json["base"], json["rates"]
            date_cache[base_currency][date] = rates
            cache.set("conversion_rates", date_cache)

        # Calculate the amount
        self.main_amount = round(
            self.base_amount / date_cache[target_currency][date][self.base_currency],
            2,
        )

    @classmethod
    def get_from_id(cls, id: int, user: User) -> Transaction | None:
        """Get transaction by id and check if it belongs to specified user.

        Args:
            id (int): id of transaction

        Returns:
            Transaction: transaction found
        """
        return cls.query.filter_by(id=id, user=user).first()


class Bank(db.Model):
    __tablename__ = "banks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, index=True, unique=True, nullable=False)
    statement_type = db.Column(db.String(10), nullable=False)

    transactions = db.relationship(
        "Transaction", back_populates="bank", lazy=True, uselist=True
    )

    def __repr__(self) -> str:
        return f"Bank: {self.name}"


class Category(db.Model, UpdatableMixin):
    __tablename__ = "categories"
    __table_args__ = (
        UniqueConstraint("name", "user_id", name="unique_user_category_key"),
    )

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(
        db.Text,
        CheckConstraint(
            # Single chain of characters/digits
            # with no whitespaces (foreign characters included)
            "name ~ '^[\u00BF-\u1FFF\u2C00-\uD7FF\w]+$'",
            name="single_word_name_check",
        ),
        index=True,
        nullable=False,
    )
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    user = db.relationship("User", back_populates="categories", lazy=True)
    transactions = db.relationship("Transaction", back_populates="category", lazy=True)

    def __repr__(self) -> str:
        return f"Category: {self.name}"

    @classmethod
    def get_from_id(cls, category_id: int, user: User) -> Category | None:
        """Query for Category with an id"""
        return cls.query.filter_by(id=category_id, user=user).first()


currencies = ["USD", "EUR", "PLN"]
table = Table(
    "currencies",
    db.metadata,
    Column("id", Integer, primary_key=True),
    *((Column(currency), Float) for currency in currencies),
)


class Currency(db.Model):
    pass


mapper(table, Currency)
