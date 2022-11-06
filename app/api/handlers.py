from marshmallow.exceptions import ValidationError

from app.api import blueprint
from app.api.utils import JSONType


@blueprint.errorhandler(ValidationError)
def validation_error(error: ValidationError) -> tuple[JSONType, int]:
    return {
        "code": 400,
        "message": "Information provided in the request contains errors",
        "errors": error.messages,
    }, 400
