from __future__ import annotations

from wallit import db, login

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, current_user
from flask import abort
from sqlalchemy import UniqueConstraint, CheckConstraint, select
from sqlalchemy.orm import with_parent
from datetime import datetime
from typing import Any, Optional


class User(UserMixin, db.Model):
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

    def __init__(self, password: str, **kwargs: dict[str, Any]) -> None:
        super(User, self).__init__(**kwargs)
        self.set_password(password)

    def __repr__(self) -> str:
        return f"{self.username}: {self.first_name} {self.last_name} under email: {self.email}"

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def select_categories(self):
        return Category.query.where(with_parent(self, User.categories)).all()

    def select_banks(self):
        return (
            Bank.query.select_from(Transaction)
            .join(Bank)
            .filter(Transaction.user == self)
            .distinct()
            .all()
        )

    def select_base_currencies(self):
        return db.session.scalars(
            select(Transaction.base_currency)
            .where(with_parent(self, User.transactions))
            .distinct()
        ).all()


@login.user_loader
def load_user(id: str) -> User:
    return User.query.get(int(id))


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.Text, index=True)
    title = db.Column(db.Text)
    main_amount = db.Column(db.Float, index=True, nullable=False)
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

    def __repr__(self) -> str:
        return f"Transaction: {self.base_amount} {self.base_currency} on {self.transaction_date}"

    @classmethod
    def get_from_id(cls, id: int, user: User) -> Transaction:
        """Get transaction by id and check if it belongs to specified user. Abort in case user/id is incorrect.

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

    @classmethod
    def get_from_name(cls, bank_name: str) -> Optional[Bank]:
        """Query for Bank with a name"""
        return cls.query.filter_by(name=bank_name).first()


class Category(db.Model):
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
    def get_from_name(cls, category_name: str, user: User) -> Optional[Category]:
        """Query for Category with a name"""
        return cls.query.filter_by(name=category_name, user=user).first()

    @classmethod
    def get_from_id(cls, category_id: str, user: User) -> Optional[Category]:
        """Query for Category with a name"""
        return cls.query.filter_by(id=category_id, user=user).first()
