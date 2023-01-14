import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from loguru import logger
from sqlalchemy import MetaData

from config import Config

DEBUG_HIGH = logger.level("DEBUG_HIGH", no=8)


metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s",
    }
)
db = SQLAlchemy(metadata=metadata)
migrate = Migrate()
ma = Marshmallow()
login = LoginManager()
login.login_view = "main.welcome"
csrf = CSRFProtect()
cache = Cache()


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    login.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)

    from app.main import blueprint as main_blueprint

    app.register_blueprint(main_blueprint)

    from app.api import blueprint as api_blueprint

    app.register_blueprint(api_blueprint)  # url_prefix defined in view functions

    from app.errors import blueprint as errors_blueprint

    app.register_blueprint(errors_blueprint)

    logger.remove()
    logger.add(
        sys.stderr,
        level="DEBUG",
        format="<BLUE>{time:HH:mm:ss} | {level} | {name}:{function}:{line}</BLUE>\n"
        "<cyan>{message}</cyan>",
        colorize=True,
    )

    if app.config["LOG_TO_STDOUT"]:
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
    else:
        Path("./logs").mkdir(exist_ok=True)
        file_handler = RotatingFileHandler(
            "logs/wallit.log", maxBytes=10240, backupCount=10
        )
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s: %(message)s " "[in %(pathname)s:%(lineno)d]"
            )
        )
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

    return app


from app import models
