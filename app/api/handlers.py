from marshmallow.exceptions import ValidationError
from flask.typing import ResponseReturnValue

from app.api import blueprint


@blueprint.errorhandler(ValidationError)
def validation_error(error: ValidationError) -> ResponseReturnValue:
    return {
        "code": 400,
        "message": "Information provided in the request contains errors",
        "errors": error.messages,
    }, 400
