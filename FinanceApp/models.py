#!python3

from FinanceApp import db, login

from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin

from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    passwordHash = db.Column(db.Text, nullable=False)
    firstName = db.Column(db.Text)
    lastName = db.Column(db.Text)

    # model name used for relationship()!
    transactions = db.relationship(
        "Transaction",
        cascade="all, delete",
        passive_deletes=True,
        backref="user",
        lazy=True,
    )
    categories = db.relationship(
        "Category",
        cascade="all, delete",
        passive_deletes=True,
        backref="user",
        lazy=True,
    )

    def __init__(self, password: str, **kwargs) -> None:
        super(User, self).__init__(**kwargs)
        self.setPassword(password)

    def __repr__(self) -> str:
        return f"{self.username}: {self.firstName} {self.lastName} under email: {self.email}"

    def setPassword(self, password: str) -> None:
        self.passwordHash = generate_password_hash(password)

    def checkPassword(self, password: str) -> bool:
        return check_password_hash(self.passwordHash, password)


@login.user_loader
def loadUser(id: str) -> User:
    return User.query.get(int(id))


class Transaction(db.Model):
    __tablename__ = "transactions"

    id = db.Column(db.Integer, primary_key=True)
    info = db.Column(db.Text, index=True)
    title = db.Column(db.Text)
    amount = db.Column(db.Float, index=True, nullable=False)
    currency = db.Column(db.Text, index=True, nullable=False)
    srcAmount = db.Column(db.Float)
    srcCurrency = db.Column(db.Text)
    transactionDate = db.Column(
        db.DateTime, index=True, nullable=False, default=datetime.utcnow
    )
    place = db.Column(db.Text)

    # table name used for ForeignKey()!
    categoryId = db.Column(db.Integer, db.ForeignKey("categories.id"), index=True)
    userId = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    bankId = db.Column(db.Integer, db.ForeignKey("banks.id"), nullable=False)

    def __repr__(self) -> str:
        return f"Transaction: {self.amount} {self.currency} on {self.transactionDate}"

    def printToTable(self) -> dict:

        return {
            "info": self.info,
            "title": self.title,
            "amount": self.amount,
            "currency": self.currency,
            "category": self.categoryId,
            "date": self.transactionDate.strftime("%Y/%m/%d %H:%M:%S"),
            "bank": self.bankId,
        }


class Bank(db.Model):
    __tablename__ = "banks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, index=True, unique=True, nullable=False)

    # model name used for relationship()!
    banks = db.relationship("Transaction", backref="bank", lazy=True)

    def __repr__(self) -> str:
        return f"Bank: {self.name}"


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, index=True, nullable=False)

    # table name used for ForeignKey()!
    userId = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"Category: {self.name}"
