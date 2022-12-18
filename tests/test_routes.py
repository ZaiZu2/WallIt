from flask import url_for, session
from flask_login import current_user, login_user
from flask.testing import FlaskClient
from unittest.mock import patch

from app.models import User


def test_succesful_login(client: FlaskClient, user_1: User) -> None:
    with client:
        assert current_user.is_anonymous
        response = client.post(
            url_for("main.login"),
            follow_redirects=True,
            data=dict(username="username1", password="password1"),
        )
        assert current_user.is_authenticated
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Log out" in html


def test_unsuccessful_login(client: FlaskClient, user_1: User) -> None:
    with client:
        assert current_user.is_anonymous
        response = client.post(
            url_for("main.login"),
            follow_redirects=True,
            data=dict(username="wrong", password="wrong"),
        )
        assert current_user.is_anonymous
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Sign in" in html


def test_logout(client: FlaskClient, user_1: User) -> None:
    with client:
        login_user(user_1)
        assert current_user.is_authenticated
        client.get(url_for("main.logout"), follow_redirects=True)
        assert current_user.is_anonymous


def test_request_reset_password(client: FlaskClient, user_1: User) -> None:
    """Test behavior when correct/wrong email address is input in reset password form"""

    with client as client, patch(
        "app.main.routes.send_password_reset_email"
    ) as send_email_mock:
        client.post(
            url_for("main.request_reset_password"), data=dict(email=user_1.email)
        )
        assert send_email_mock.call_count == 1

        client.post(
            url_for("main.request_reset_password"), data=dict(email="wrong_email")
        )
        assert send_email_mock.call_count == 1


def test_reset_password(client: FlaskClient, user_1: User) -> None:
    """Test reset password edpoint generated with unique token"""

    token = user_1.get_reset_password_token()

    with client:
        # Check successful web page load
        response = client.get(
            url_for("main.reset_password", token=token, _external=True)
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Reset password" in html

        # Check successful password change
        client.post(
            url_for("main.reset_password", token=token, _external=True),
            follow_redirects=True,
            data=dict(password="new_password", repeat_password="new_password"),
        )
        assert user_1.check_password("new_password")


def test_sign_up(client: FlaskClient, user_1: User) -> None:
    with client:
        # Sign up with already used username/email
        response = client.post(
            url_for("main.sign_up"),
            data=dict(
                username=user_1.username,
                email=user_1.email,
                password="password2",
                repeat_password="password2",
            ),
            follow_redirects=True,
        )
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert "Username is already used" in html
        assert "Email is already used" in html

        # Successful sign-up
        client.post(
            url_for("main.sign_up"),
            data=dict(
                username="username2",
                email="email2@gmail.com",
                password="password2",
                repeat_password="password2",
            ),
            follow_redirects=True,
        )
        assert User.query.filter_by(username="username2").first()
