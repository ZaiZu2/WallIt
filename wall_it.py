from turtle import color
from wallit import app, db, login

from wallit.models import User, Transaction, Bank

import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<BLUE>{time:HH:mm:ss} | {level} | {name}:{function}:{line}</BLUE>\n"
    "<cyan>{message}</cyan>",
    colorize=True,
)


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
