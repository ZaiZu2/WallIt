from flask import render_template, current_app
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.models import User
from app.exceptions import ExternalApiError


def send_password_reset_email(user: User) -> None:

    token = user.get_reset_password_token()
    message = Mail(
        from_email="qba200@gmail.com",
        to_emails=user.email,
        subject="WallIt - password reset request",
        plain_text_content=render_template("email/reset_password.txt", token=token),
        html_content=render_template("email/reset_password.html", token=token),
    )

    sg = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
    sg.send(message)
