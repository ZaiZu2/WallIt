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

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
login = LoginManager()
login.login_view = "main.welcome"
csrf = CSRFProtect()
cache = Cache()
mail = Mail()


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app)
    ma.init_app(app)
    login.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    mail.init_app(app)

    from app.main import blueprint as main_blueprint

    app.register_blueprint(main_blueprint)

    from app.api import blueprint as api_blueprint

    app.register_blueprint(api_blueprint)  # url_prefix defined in view functions

    return app


from app import models, handlers
