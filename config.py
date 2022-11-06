#! python3

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "less_secret_key"

    # postgres
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "postgresql://jakub:admin@localhost:5432/wallit"
    )
    # #sqlite3
    # SQLALCHEMY_DATABASE_URI = (
    #     os.environ.get("DATABASE_URL")
    #     or "sqlite:///C:/Users/z0043xev/Git/WallIt/database/data.db"
    # )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    MAX_CONTENT_LENGTH = 1024 * 1024

    # Cache config
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 3600

    # Flask-mail config
    MAIL_SERVER = os.environ.get("MAIL_SERVER") or "localhost"
    MAIL_PORT = int(os.environ.get("MAIL_PORT") or 8025)
    # MAIL_USE_TLS = int(os.environ.get('MAIL_USE_TLS') or 1)
    # MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    ADMINS = ["donotreply@wallit.com"]

    RESET_TOKEN_MINUTES = int(os.environ.get("RESET_TOKEN_MINUTES") or "15")

    # Currency conversion API
    CURRENCYSCOOP_API_KEY = (
        os.environ.get("CURRENCYSCOOP_API_KEY") or "39c83a7c50bb795501ee384a76c18cac"
    )
