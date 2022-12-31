from app import create_app, db, login
from app.models import User, Transaction, Bank, Category, ExchangeRate
from app.cli import commands

app = create_app()
commands.register(app)


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
