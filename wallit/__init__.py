#! python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from config import Config

import sys
from loguru import logger

logger.remove()
logger.add(
    sys.stderr,
    format="<BLUE>{time:HH:mm:ss} | {level} | {name}:{function}:{line}</BLUE>\n"
    "<cyan>{message}</cyan>",
    colorize=True,
)

app = Flask(__name__)
app.config.from_object(Config)  # read flask app config file

csrf = CSRFProtect(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "welcome"

from wallit import routes, models
