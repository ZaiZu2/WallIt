#! python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import Config

from loguru import logger

app = Flask(__name__)
app.config.from_object(Config)  # read flask app config file

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = "welcome"

from wallit import routes, models
