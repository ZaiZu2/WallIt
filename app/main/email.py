from flask import render_template, current_app
from flask_mail import Message

from app.models import User
from app import mail


def send_password_reset_email(user: User) -> None:

    token = user.get_reset_password_token()
    message = Message(
        subject="WallIt - password reset request",
        recipients=[user.email],
        body=render_template("email/reset_password.txt", token=token),
        html=render_template("email/reset_password.html", token=token),
        sender=current_app.config["ADMINS"][0],
    )
    mail.send(message)
