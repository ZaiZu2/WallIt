from flask import abort, request
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required

from app import db
from app.api import blueprint
from app.api.schemas import CategorySchema, UniqueCategorySchema
from app.models import Category


@blueprint.route("/api/categories/add", methods=["POST"])
@login_required
def add_category() -> ResponseReturnValue:
    """Add a category"""

    verified_data = UniqueCategorySchema().load(request.json)
    category = Category(user=current_user, **verified_data)
    db.session.add(category)
    db.session.commit()
    return CategorySchema().dump(category), 201


@blueprint.route("/api/categories/<int:id>/modify", methods=["PATCH"])
@login_required
def modify_category(id: int) -> ResponseReturnValue:
    """Modify a category"""

    if not (category := Category.get_from_id(id, current_user)):
        abort(404, "Category not found")
    verified_data = CategorySchema().load(request.json)
    category.update(verified_data)
    db.session.commit()
    return CategorySchema().dump(category), 201


@blueprint.route("/api/categories/<int:id>/delete", methods=["DELETE"])
@login_required
def delete_category(id: int) -> ResponseReturnValue:
    """Delete a category"""

    if not (category := Category.get_from_id(id, current_user)):
        abort(404, "Category not found")
    db.session.delete(category)
    db.session.commit()

    return CategorySchema().dump(category), 200
