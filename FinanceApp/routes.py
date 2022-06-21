#! python3

from FinanceApp import app
from FinanceApp.forms import LoginForm, SignUpForm, ResetPasswordForm
from FinanceApp.models import User

from flask import redirect, request, url_for, render_template, flash
from flask_login import current_user, login_required, login_user, logout_user


@app.route("/")
@login_required
def index():
    currencies = ["CZK", "PLN", "EUR", "USD"]
    categories = ["Groceries", "Salary", "Entertainment", "Hobby", "Restaurant", "Rent"]
    banks = ["Equabank", "mBank", "Revolut"]

    class User:
        def __init__(self) -> None:
            name = "Kuba"

    user1 = User()

    return render_template(
        "filter.html",
        user=user1,
        currencies=currencies,
        categories=categories,
        banks=banks,
        current_user=current_user._get_current_object(),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    loginForm = LoginForm()
    if loginForm.validate_on_submit():
        user = User.query.filter_by(username=loginForm.username.data).first()
        if user is None or not user.checkPassword(loginForm.password.data):
            flash("Invalid username or password")
            return redirect(url_for("login"))
        login_user(user, remember=loginForm.rememberMe.data)
        return redirect(url_for("index"))

    return render_template(
        "welcome_context.html", loginForm=loginForm, path=request.path
    )


@app.route("/account/reset", methods=["GET", "POST"])
def resetPassword():
    resetPasswordForm = ResetPasswordForm()
    if resetPasswordForm.validate_on_submit():
        return redirect(url_for("resetPassword"))

    return render_template(
        "welcome_context.html", resetPasswordForm=resetPasswordForm, path=request.path
    )


@app.route("/account/new", methods=["GET", "POST"])
def signUp():
    signUpForm = SignUpForm()
    if signUpForm.validate_on_submit():
        return redirect(url_for("signUp"))

    return render_template(
        "welcome_context.html", signUpForm=signUpForm, path=request.path
    )


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))
