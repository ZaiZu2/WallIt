#! python3

import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or "less_secret_key"

    # postgres
    # SQLALCHEMY_DATABASE_URI = (
    #     os.environ.get("DATABASE_URL")
    #     or "postgresql://zaizu:admin@localhost:5433/wallit"
    # )
    #sqlite3
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or "sqlite:///C:/Users/z0043xev/Git/WallIt/database/data.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    MAX_CONTENT_LENGTH = 1024 * 1024

    # Currency conversion API
    CURRENCYSCOOP_API_KEY = (
        os.environ.get("CURRENCYSCOOP_API_KEY") or "39c83a7c50bb795501ee384a76c18cac"
    )
