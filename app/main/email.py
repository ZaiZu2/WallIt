from flask import current_app, render_template
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from app.exceptions import ExternalApiError
from app.models import User


def send_password_reset_email(user: User) -> None:

    token = user.get_reset_password_token()
    message = Mail(
        from_email=current_app.config["AUTOMATED_EMAIL"],
        to_emails=user.email,
        subject="WallIt - password reset request",
        plain_text_content=render_template("email/reset_password.txt", token=token),
        html_content=render_template("email/reset_password.html", token=token),
    )

    sg = SendGridAPIClient(current_app.config["SENDGRID_API_KEY"])
    try:
        sg.send(message)
    except Exception as error:
        print(error)
