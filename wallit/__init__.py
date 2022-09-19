#! python3

from config import Config

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail

import sys
from loguru import logger

logger.remove()
DEBUG_HIGH = logger.level("DEBUG_HIGH", no=8)
logger.add(
    sys.stderr,
    level="DEBUG",
    format="<BLUE>{time:HH:mm:ss} | {level} | {name}:{function}:{line}</BLUE>\n"
    "<cyan>{message}</cyan>",
    colorize=True,
)

app = Flask(__name__)
app.config.from_object(Config)  # read flask app config file

db = SQLAlchemy(app)
migrate = Migrate(app, db)
ma = Marshmallow(app)

csrf = CSRFProtect(app)
cache = Cache(app)
login = LoginManager(app)
login.login_view = "welcome"
mail = Mail(app)

from wallit import routes, models
