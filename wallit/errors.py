from wallit import app
from wallit.helpers import JSONType

from marshmallow.exceptions import ValidationError
from werkzeug.exceptions import HTTPException


@app.errorhandler(HTTPException)
def http_error(error: HTTPException) -> tuple[JSONType, int]:
    return {
        "code": error.code,
        "message": error.name,
        "description": error.description,
    }, error.code


@app.errorhandler(ValidationError)
def validation_error(error: ValidationError) -> tuple[JSONType, int]:
    return {
        "code": 400,
        "message": "Information provided in the request contains errors",
        "errors": error.messages,
    }, 400
