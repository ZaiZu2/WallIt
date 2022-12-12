from flask import request, abort
from flask_login import current_user, login_required

from app import db
from app.api import blueprint
from app.models import Category
from app.api.schemas import CategorySchema
from app.api.utils import JSONType


@blueprint.route("/api/categories/add", methods=["POST"])
@login_required
def add_category() -> tuple[JSONType, int]:
    """Add category"""

    verified_data = CategorySchema().load(request.json)
    category = Category(user=current_user, **verified_data)
    db.session.add(category)
    db.session.commit()
    return CategorySchema().dumps(category), 201


@blueprint.route("/api/categories/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_category(id: int) -> tuple[JSONType, int]:
    """Modify category"""

    if not (category := Category.get_from_id(id, current_user)):
        abort(404)
    verified_data = CategorySchema().load(request.json)
    category.update(verified_data)
    db.session.commit()
    return CategorySchema().dumps(category), 201


# TODO: Delete and replace with single category delete
@blueprint.route("/api/categories/delete", methods=["DELETE"])
@login_required
def delete_categories() -> tuple[JSONType, int]:
    """Delete multiple categories"""

    verified_data = CategorySchema(many=True).load(request.json, partial=True)

    deleted_categories = []
    for category in verified_data:
        if category := Category.get_from_id(category["id"], current_user):
            deleted_categories.append(category)

    for deleted_category in deleted_categories:
        db.session.delete(deleted_category)
    db.session.commit()

    return CategorySchema(many=True).dumps(deleted_categories), 201


@blueprint.route("/api/categories/<int:id>delete", methods=["DELETE"])
@login_required
def delete_category(id: int) -> tuple[JSONType, int]:
    """Delete multiple categories"""

    if not (category := Category.get_from_id(id, current_user)):
        abort(404)
    db.session.delete(category)
    db.session.commit()

    return CategorySchema().dumps(category), 201
