from werkzeug.exceptions import HTTPException

from app.api import blueprint
from app.api.utils import JSONType


@blueprint.errorhandler(HTTPException)
def http_error(error: HTTPException) -> tuple[JSONType, int]:
    return {
        "code": error.code,
        "message": error.name,
        "description": error.description,
    }, error.code
