#! python3

import email
from FinanceApp import app, db
from FinanceApp.forms import LoginForm, SignUpForm, ResetPasswordForm
from FinanceApp.models import User

from flask import redirect, request, session, url_for, render_template, flash
from flask_login import current_user, login_required, login_user, logout_user


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


@app.route("/welcome", methods=["GET", "POST"])
def welcome():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        return redirect(url_for("login"))

    signUpForm = SignUpForm()
    if signUpForm.validate_on_submit():
        return redirect(url_for("signUp"))

    resetPasswordForm = ResetPasswordForm()
    if resetPasswordForm.validate_on_submit():
        return redirect(url_for("passwordReset"))

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
            flash("Invalid username or password")
            return redirect(url_for("welcome"))

        login_user(user, remember=loginForm.rememberMe.data)
        return redirect(url_for("index"))

    return redirect(url_for("welcome"))


@app.route("/account/reset", methods=["POST"])
def passwordReset():
    pass
    # query the db for email address
    # send email with password


@app.route("/account/new", methods=["POST"])
def signUp():
    signUpForm = SignUpForm()
    if signUpForm.validate_on_submit():
        if User.query.filter_by(username=signUpForm.username.data).first():
            flash("Username is already used")
            return redirect(url_for("welcome"))
        if User.query.filter_by(email=signUpForm.email.data).first():
            flash("Email is already used")
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
        flash("Account created successfully")
        return redirect(url_for("welcome"))

    flash("wrong form")
    return redirect(url_for("welcome"))


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("welcome"))
