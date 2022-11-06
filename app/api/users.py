from marshmallow import ValidationError
from flask import request, abort
from flask_login import current_user, login_required
from collections import defaultdict

from app import db
from app.models import User
from app.api import blueprint
from app.api.schemas import (
    ChangePasswordSchema,
    ModifyUserSchema,
    UserSchema,
    UserEntitiesSchema,
)
from app.api.utils import convert_currency, JSONType


@blueprint.route("/api/users/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_user(id: int) -> tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    try:
        verified_data = ModifyUserSchema().load(request.json)
    except ValidationError as error:
        return error.messages, 400

    if (
        "main_currency" in verified_data
        and verified_data["main_currency"] != user.main_currency
    ):
        convert_currency(user.select_transactions(), verified_data["main_currency"])

    user.update(verified_data)
    db.session.commit()

    return UserSchema().dumps(user), 200


@blueprint.route("/api/users/<int:id>/change_password", methods=["PATCH"])
@login_required
def change_password(id: int) -> tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    try:
        verified_data = ChangePasswordSchema().load(request.json)
    except ValidationError as error:
        return error.messages, 400

    if not user.check_password(verified_data["old_password"]):
        abort(400)
    user.set_password(verified_data["new_password"])
    db.session.commit()

    return {}, 200


@blueprint.route("/api/users/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_user(id: int) -> tuple[JSONType, int]:
    user: User = User.query.get(id)
    if user != current_user:
        abort(404)

    db.session.delete(user)
    # db.session.commit()
    return {}, 200


@blueprint.route("/api/user/entities", methods=["GET"])
@login_required
def fetch_user_entities() -> tuple[JSONType, int]:
    """Fetch entities assigned to user

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

    response_body: dict[str, list | dict] = defaultdict(dict)

    response_body["user_details"] = current_user
    response_body["base_currencies"] = current_user.select_base_currencies()
    for category in current_user.select_categories():
        response_body["categories"][category.name] = category
    for bank in current_user.select_banks():
        response_body["banks"][bank.name] = bank

    # Schema used only to map server-side 'json' names to general ones specified by schema
    return UserEntitiesSchema().dumps(response_body), 200
