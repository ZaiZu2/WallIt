import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).joinpath(".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "").replace(
        "postgres://", "postgresql://"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    MAX_CONTENT_LENGTH = 1024 * 1024

    # Cache config
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 3600

    RESET_TOKEN_MINUTES = int(os.environ.get("RESET_TOKEN_MINUTES") or "15")

    # Currency conversion API
    CURRENCYSCOOP_API_URL = "https://api.currencyscoop.com/v1/historical?api_key={key}&base={target_currency}&date={date}"
    CURRENCYSCOOP_API_KEY = os.environ.get("CURRENCYSCOOP_API_KEY")

    # Email API
    ADMINS = ["wall.it@gmail.com"]
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")

    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")
