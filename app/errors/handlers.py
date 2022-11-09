from werkzeug.exceptions import HTTPException
from flask import render_template, request

from app.errors import blueprint


@blueprint.app_errorhandler(HTTPException)
def http_error(error: HTTPException) -> tuple[dict, int]:
    return {
        "code": error.code,
        "message": error.name,
        "description": error.description,
    }, error.code


# @blueprint.errorhandler(404)
# def not_found(error: HTTPException) -> tuple[dict, int]:
#     if request.accept_mimetypes.accept_json:
#         return {
#             "code": error.code,
#             "message": error.name,
#             "description": error.description,
#         }, error.code
#     else:
