from app import create_app, db, login
from app.models import User, Transaction, Bank, Category, ExchangeRate
import cli

app = create_app()
cli.register(app)


@app.shell_context_processor
def make_shell_context() -> dict:
    return {
        "db": db,
        "login": login,
        "User": User,
        "Transaction": Transaction,
        "Bank": Bank,
        "Category": Category,
        "ExchangeRate": ExchangeRate,
    }


if __name__ == "__main__":
    app.run()
