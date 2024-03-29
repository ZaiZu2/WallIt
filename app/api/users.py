from collections import defaultdict

from flask import abort, request
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required

from app import db
from app.api import blueprint
from app.api.schemas import (
    ChangePasswordSchema,
    ModifyUserSchema,
    UserEntitiesSchema,
    UserSchema,
)
from app.models import User


@blueprint.route("/api/users/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_user(id: int) -> ResponseReturnValue:
    user: User = User.query.get(id)
    if user is None or user != current_user:
        abort(404, "User not found")

    verified_data = ModifyUserSchema().load(request.json)
    user.update(verified_data)
    db.session.commit()

    return UserSchema().dump(user), 200


@blueprint.route("/api/users/<int:id>/change_password", methods=["PATCH"])
@login_required
def change_password(id: int) -> ResponseReturnValue:
    user = User.query.get(id)
    if user is None or user != current_user:
        abort(404, "User not found")

    verified_data = ChangePasswordSchema().load(request.json)
    if not user.check_password(verified_data["old_password"]):
        abort(403, "Wrong password")
    user.set_password(verified_data["new_password"])
    db.session.commit()

    return {}, 204


@blueprint.route("/api/users/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_user(id: int) -> ResponseReturnValue:
    user = User.query.get(id)
    if user is None or user != current_user:
        abort(404, "User not found")

    db.session.delete(user)
    db.session.commit()
    return {}, 204


@blueprint.route("/api/user/entities", methods=["GET"])
@login_required
def fetch_user_entities() -> ResponseReturnValue:
    """Fetch entities assigned to a user

    Response JSON structure example:
    {
        "bank": ["Equabank", "Revolut", ...],
        "base_currency": ["EUR", "CZK", "USD", ...],
        "category": ["groceries", "restaurant", "salary", ...],
        "currency_codes": ["USD", "EUR", "CZK", ...]
    }

    Returns:
        dict: lists containing values for each filtering parameter
    """

    response_body: dict[str, dict] = defaultdict(dict)

    response_body["user_details"] = current_user
    response_body["base_currencies"] = current_user.select_base_currencies()
    for category in current_user.select_categories():
        response_body["categories"][category.name] = category
    for bank in current_user.select_banks():
        response_body["banks"][bank.name] = bank

    # Schema used only to map server-side 'json' names to general ones specified by schema
    return UserEntitiesSchema().dump(response_body), 200
