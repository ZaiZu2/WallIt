from wallit import app, db, login
from wallit.models import User, Transaction, Bank, Category

from typing import Any


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


if __name__ == "__main__":
    app.run()
