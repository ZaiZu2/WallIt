from flask import render_template
from flask.typing import ResponseReturnValue
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.exceptions import HTTPException

from app import db
from app.errors import blueprint


@blueprint.app_errorhandler(HTTPException)
def http_error(error: HTTPException) -> ResponseReturnValue:
    return {
        "code": error.code,
        "message": error.description,
    }, error.code


@blueprint.app_errorhandler(SQLAlchemyError)
def sqlalchemy_error(error: SQLAlchemyError) -> ResponseReturnValue:
    db.session.rollback()
    return render_template("error500.html"), 500


@blueprint.app_errorhandler(500)
def error_500(error: HTTPException) -> ResponseReturnValue:
    return render_template("error500.html"), 500


@blueprint.app_errorhandler(404)
def error_404(error: HTTPException) -> ResponseReturnValue:
    return render_template("error404.html"), 404
