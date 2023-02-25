from flask import render_template
from flask.typing import ResponseReturnValue
from marshmallow.exceptions import ValidationError
from werkzeug.exceptions import HTTPException

from app.api import blueprint


@blueprint.errorhandler(ValidationError)
def validation_error(error: ValidationError) -> ResponseReturnValue:
    return {
        "code": 400,
        "message": "Information provided in the request contains errors",
        "errors": error.messages,
    }, 400


@blueprint.errorhandler(HTTPException)
def http_error(error: HTTPException) -> tuple[dict, int]:
    return {
        "code": error.code,
        "message": error.description,
    }, error.code
