from app import create_app, db, login
from app.models import User, Transaction, Bank, Category

from typing import Any

app = create_app()


@app.shell_context_processor
def make_shell_context() -> dict[str, Any]:
    return {
        "db": db,
        "login": login,
        "User": User,
        "Transaction": Transaction,
        "Bank": Bank,
        "Category": Category,
    }
