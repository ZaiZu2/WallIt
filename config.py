#! python3

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "less_secret_key"

    # postgresql://[user[:password]@][netloc][:port][/dbname][?param1=value1&...]
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql://zaizu:admin@localhost:5433/wallit"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
