from flask import url_for
from flask.testing import FlaskClient

from app.models import Bank, Category, Transaction, User
from tests.conftest import login


def test_modify_user(client: FlaskClient, user_1: User) -> None:
    with client:
        # Check successful call
        login(user_1, client)
        response = client.patch(
            url_for("api.modify_user", id=user_1.id),
            json=dict(first_name="firstTwo", last_name="lastTwo"),
        )
        assert response.status_code == 200
        assert user_1.first_name == response.json["first_name"] == "firstTwo"
        assert user_1.last_name == response.json["last_name"] == "lastTwo"

        # Check wrong user id
        response = client.patch(
            url_for("api.modify_user", id=2),
            json=dict(first_name="firstThree", last_name="lastThree"),
        )
        assert response.status_code == 404


def test_change_password(client: FlaskClient, user_1: User) -> None:
    with client:
        login(user_1, client)
        # Successful change
        client.patch(
            url_for("api.change_password", id=user_1.id),
            json=dict(
                old_password="password1",
                new_password="password2",
                repeat_password="password2",
            ),
        )
        assert user_1.check_password("password2")

        # Wrong user ID
        response = client.patch(
            url_for("api.change_password", id=2),
            json=dict(),
        )
        assert response.status_code == 404

        # Wrong old password
        response = client.patch(
            url_for("api.change_password", id=user_1.id),
            json=dict(
                old_password="password1",
                new_password="password3",
                repeat_password="password3",
            ),
        )
        assert response.status_code == 400
        assert user_1.check_password("password2")


def test_successful_delete_user(client: FlaskClient, user_1: User) -> None:
    with client:
        # Check successful call
        login(user_1, client)
        response = client.delete(url_for("api.delete_user", id=user_1.id))
        assert response.status_code == 200
        assert User.query.get(user_1.id) == None


def test_unsuccessful_delete_user(client: FlaskClient, user_1: User) -> None:
    with client:
        # Wrong user ID
        login(user_1, client)
        response = client.delete(url_for("api.delete_user", id=99999))
        assert response.status_code == 404


def test_fetch_user_entities(
    client: FlaskClient,
    user_1: User,
    bank_1: Bank,
    category_1: Category,
    transaction_1: Transaction,
) -> None:
    with client:
        login(user_1, client)
        response = client.get(url_for("api.fetch_user_entities"))
        assert response.status_code == 200
        assert response.json["banks"][bank_1.name] == {
            "id": bank_1.id,
            "name": bank_1.name,
        }
        assert response.json["categories"][category_1.name] == {
            "id": category_1.id,
            "name": category_1.name,
        }
