#! python3

from flask import redirect, url_for
from FinanceApp import app, Database
from FinanceApp.forms import LoginForm, SignUpForm, ResetPasswordForm

from flask import render_template, flash


@app.route("/")
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
    )


@app.route("/login", methods=["GET", "POST"])
def login():

    loginForm = LoginForm()
    signUpForm = SignUpForm()
    resetPasswordForm = ResetPasswordForm()

    if loginForm.validate_on_submit():
        print("LOGIN")
        flash(
            "Login requested for user {}, remember_me={}".format(
                loginForm.username.data, loginForm.rememberMe.data
            )
        )
        # logic authorizing the user
        return redirect(url_for("index"))

    if signUpForm.validate_on_submit():
        print("SIGNUP")
        return redirect(url_for("signUp"))

    return render_template(
        "login.html",
        loginForm=loginForm,
        signUpForm=signUpForm,
        resetPasswordForm=resetPasswordForm,
    )


@app.route("/account/reset", methods=["POST"])
def passwordReset():

    pass
    # query the db for email address
    # send email with password


@app.route("/account/new", methods=["POST"])
def signUp():

    pass
