from flask import flash, redirect, render_template, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.wrappers import Response

from app import db
from app.main import blueprint
from app.main.email import send_password_reset_email
from app.main.forms import LoginForm, RequestPasswordForm, ResetPasswordForm, SignUpForm
from app.models import User


@blueprint.route("/index")
@blueprint.route("/")
@login_required
def index() -> str:
    return render_template(
        "index.html", current_user=current_user._get_current_object()
    )


@blueprint.route("/welcome", methods=["GET"])
def welcome() -> str | Response:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    login_form = LoginForm()
    sign_up_form = SignUpForm()
    request_password_form = RequestPasswordForm()

    return render_template(
        "menus.html",
        login_form=login_form,
        sign_up_form=sign_up_form,
        request_password_form=request_password_form,
    )


@blueprint.route("/login", methods=["POST"])
def login() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    login_form = LoginForm()
    if login_form.validate_on_submit():
        user = User.query.filter_by(username=login_form.username.data).first()
        if user is None or not user.check_password(login_form.password.data):
            flash("Invalid username or password", "login_message")
            return redirect(url_for("main.welcome"))

        login_user(user, remember=login_form.remember_me.data)
        return redirect(url_for("main.index"))

    # Reassing form.errors to flash as they will be inaccessible after after redirection
    for field in login_form._fields.values():
        for error in field.errors:
            flash(error, "login_message")
    return redirect(url_for("main.welcome"))


@blueprint.route("/logout", methods=["GET"])
@login_required
def logout() -> Response:
    logout_user()
    return redirect(url_for("main.welcome"))


@blueprint.route("/reset_password", methods=["POST"])
def request_reset_password() -> Response:
    request_password_form = RequestPasswordForm()
    if request_password_form.validate_on_submit():
        if user := User.query.filter_by(email=request_password_form.email.data).first():
            send_password_reset_email(user)
        flash("Email with password reset form was sent", "reset_password_message")
        return redirect(url_for("main.welcome"))

    # Reassign form.errors to flash as they will be inaccessible after redirection
    for field in request_password_form._fields.values():
        for error in field.errors:
            flash(error, "reset_password_message")
    return redirect(url_for("main.welcome"))


@blueprint.route("/reset_password/<string:token>", methods=["GET", "POST"])
def reset_password(token: str) -> str | Response:
    user = User.verify_reset_password_token(token)
    if user is None:
        return redirect(url_for("main.welcome"))
    reset_password_form = ResetPasswordForm()
    if reset_password_form.validate_on_submit():
        user.set_password(reset_password_form.password.data)
        db.session.commit()
        flash("Password has been successfully reset", "login_message")
        return redirect(url_for("main.logout"))
    return render_template(
        "reset_password.html", reset_password_form=reset_password_form
    )


@blueprint.route("/users/add", methods=["POST"])
def sign_up() -> Response:
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    sign_up_form = SignUpForm()
    if sign_up_form.validate_on_submit():
        param_taken = False
        if User.query.filter_by(username=sign_up_form.username.data).first():
            flash("Username is already used", "sign_up_message")
            param_taken = True
        if User.query.filter_by(email=sign_up_form.email.data).first():
            flash("Email is already used", "sign_up_message")
            param_taken = True
        if param_taken:
            return redirect(url_for("main.welcome"))

        new_user = User(
            username=sign_up_form.username.data,
            email=sign_up_form.email.data,
            password=sign_up_form.password.data,
            first_name=sign_up_form.first_name.data,
            last_name=sign_up_form.last_name.data,
        )
        db.session.add(new_user)
        db.session.commit()
        flash("Account created successfully", "sign_up_message")
        return redirect(url_for("main.welcome"))

    # Reassign form.errors to flash as they will be inaccessible after redirection
    for field in sign_up_form._fields.values():
        for error in field.errors:
            flash(error, "sign_up_message")
    return redirect(url_for("main.welcome"))
