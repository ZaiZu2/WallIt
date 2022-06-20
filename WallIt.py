from FinanceApp import app, db, login

from FinanceApp.models import User, Transaction, Bank


@app.shell_context_processor
def make_shell_context():
    return {
        "db": db,
        "login": login,
        "User": User,
        "Transaction": Transaction,
        "Bank": Bank,
    }


if __name__ == "__main__":
    app.run()
