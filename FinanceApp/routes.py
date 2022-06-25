#! python3


from sqlalchemy import select
from FinanceApp import app, db
from FinanceApp.forms import LoginForm, SignUpForm, ResetPasswordForm
from FinanceApp.models import Transaction, User, Bank, Category

from flask import redirect, request, session, url_for, render_template, flash
from flask_login import current_user, login_required, login_user, logout_user

from datetime import datetime


@app.route("/")
@login_required
def index():
    currencies = ["CZK", "PLN", "EUR", "USD"]
    categories = ["Groceries", "Salary", "Entertainment", "Hobby", "Restaurant", "Rent"]
    banks = ["Equabank", "mBank", "Revolut"]

    return render_template(
        "index.html",
        currencies=currencies,
        categories=categories,
        banks=banks,
        current_user=current_user._get_current_object(),
    )


@app.route("/welcome", methods=["GET"])
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    loginForm = LoginForm()
    signUpForm = SignUpForm()
    resetPasswordForm = ResetPasswordForm()

    return render_template(
        "welcome.html",
        loginForm=loginForm,
        signUpForm=signUpForm,
        resetPasswordForm=resetPasswordForm,
    )


@app.route("/login", methods=["POST"])
def login():
    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = User.query.filter_by(username=loginForm.username.data).first()
        if user is None or not user.checkPassword(loginForm.password.data):
            flash("Invalid username or password", "login")
            return redirect(url_for("welcome"))

        login_user(user, remember=loginForm.rememberMe.data)
        return redirect(url_for("index"))

    for field in loginForm._fields.values():
        for error in field.errors:
            flash(error, "login")
    return redirect(url_for("welcome"))


@app.route("/account/reset", methods=["POST"])
def resetPassword():
    resetPasswordForm = ResetPasswordForm()
    if resetPasswordForm.validate_on_submit():
        if User.query.filter_by(email=resetPasswordForm.email.data).first():
            # send email with password reset form
            flash("Email with password reset form was sent", "resetPassword")
            return redirect(url_for("welcome"))

        flash("Account with given email does not exist", "resetPassword")

    for field in resetPasswordForm._fields.values():
        for error in field.errors:
            flash(error, "resetPassword")
    return redirect(url_for("welcome"))


@app.route("/account/new", methods=["POST"])
def signUp():
    signUpForm = SignUpForm()
    if signUpForm.validate_on_submit():
        if User.query.filter_by(username=signUpForm.username.data).first():
            flash("Username is already used, 'signUp'")
            return redirect(url_for("welcome"))
        if User.query.filter_by(email=signUpForm.email.data).first():
            flash("Email is already used", "signUp")
            return redirect(url_for("welcome"))

        newUser = User(
            username=signUpForm.username.data,
            email=signUpForm.email.data,
            password=signUpForm.password.data,
            firstName=signUpForm.firstName.data,
            lastName=signUpForm.lastName.data,
        )
        db.session.add(newUser)
        db.session.commit()
        flash("Account created successfully", "signUp")
        return redirect(url_for("welcome"))

    for field in signUpForm._fields.values():
        for error in field.errors:
            flash(error, "signUp")
    return redirect(url_for("welcome"))


@app.route("/logout", methods=["GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))


@app.route("/api/transactions")
@login_required
def transactionTable():
    """Generate serialized transaction records used for populating Transaction Table

    Returns:
        dict: serialized transaction data and transaction count
    """

    # Dictionary mapping queried values to the keys used for serialization
    serializeMap = {
        "info": Transaction.info,
        "title": Transaction.title,
        "amount": Transaction.amount,
        "currency": Transaction.currency,
        "date": Transaction.transactionDate,
        "place": Transaction.place,
        "category": Category.name,
        "bank": Bank.name,
    }

    query = (
        select([dbField for dbField in serializeMap.values()])
        .filter_by(userId=current_user.id)
        .select_from(Transaction)
        .join(Bank)
        .join(Category)
    )
    results = db.session.execute(query).all()

    # Serializing data received from the DB
    tableRows = []
    for result in results:
        resultDict = {}
        for name, value in zip(serializeMap.keys(), result):
            if isinstance(value, datetime):
                resultDict[name] = value.strftime("%Y/%m/%d")
            else:
                resultDict[name] = value
        tableRows.append(resultDict)

    return {"transactions": tableRows, "total": len(tableRows)}
