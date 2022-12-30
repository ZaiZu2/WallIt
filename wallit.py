from app import create_app, db, login
from app.models import User, Transaction, Bank, Category, ExchangeRate
from app.main import cli

# from app.main.cli import load

app = create_app()
cli.register(app)
# with app.app_context():
#     # download("2022-12-13", "2022-12-13")
#     load("deployment/exchange_rates_2020-01-01_2022-12-26.csv")


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
