from .FinanceApp import app, db

from FinanceApp.models import User, Transaction, Bank


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Transaction": Transaction, "Bank": Bank}
