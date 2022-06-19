#!python3

from FinanceApp import db

from datetime import datetime


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.Text, index=True, unique=True, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    passwordHash = db.Column(db.Text, nullable=False)
    firstName = db.Column(db.Text)
    lastName = db.Column(db.Text)

    # model name used for relationship()!
    transactions = db.relationship("Transaction", backref="user", lazy=True)

    def __repr__(self) -> str:
        return f"{self.username}: {self.firstName} {self.lastName} under email: {self.email}"


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
    category = db.Column(db.Text, index=True)

    # table name used for ForeignKey()!
    userId = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    bankId = db.Column(db.Integer, db.ForeignKey("banks.id"), nullable=False)

    def __repr__(self) -> str:
        return f"Transaction: {self.amount} {self.currency} on {self.transactionDate}"


class Bank(db.Model):
    __tablename__ = "banks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, index=True, unique=True, nullable=False)

    # model name used for relationship()!
    banks = db.relationship("Transaction", backref="bank", lazy=True)

    def __repr__(self) -> str:
        return f"Bank: {self.name}"
