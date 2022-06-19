#! python3

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config


app = Flask(__name__)
app.config.from_object(Config)  # read flask app config file

db = SQLAlchemy(app)
migrate = Migrate(app, db)

from FinanceApp import routes, models
