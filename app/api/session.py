from flask_login import login_required
from collections import defaultdict

from app.models import Bank
from app.api import blueprint
from app.api.schemas import SessionEntitiesSchema
from app.api.utils import get_currencies, JSONType


@blueprint.route("/api/entities", methods=["GET"])
@login_required
def fetch_session_entities() -> tuple[JSONType, int]:
    """Get basic session data required for front-end function

    Response JSON structure example:
    {
        "currencies": ["USD", "EUR", ...],
        "banks": {
            "Revolut": {"id":1,"name":"Revolut"},
            "Equabank":{"id":2,"name":"Equabank"},
            ...
        }
    }

    Returns:
        tuple[JSONType, int]: _description_
    """
    response_body: dict[str, list | dict] = defaultdict(dict)
    response_body["currencies"] = get_currencies()
    for bank in Bank.query.all():
        response_body["banks"][bank.name] = bank

    return SessionEntitiesSchema().dumps(response_body), 200
