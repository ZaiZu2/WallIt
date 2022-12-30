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
    RESET_TOKEN_MINUTES = int(os.environ.get("RESET_TOKEN_MINUTES") or "15")
    LOG_TO_STDOUT = os.environ.get("LOG_TO_STDOUT")

    # Cache config
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 3600

    # Currency conversion API
    CURRENCYSCOOP_API_KEY = os.environ.get("CURRENCYSCOOP_API_KEY")
    CURRENCYSCOOP_HISTORICAL_URL = "https://api.currencyscoop.com/v1/historical?api_key={key}&base={target_currency}&date={date}"
    CURRENCYSCOOP_CURRENCIES_URL = (
        "https://api.currencybeacon.com/v1/currencies?api_key={key}"
    )

    # Email API
    ADMINS = ["wallit.help@gmail.com"]
    SENDGRID_API_KEY = os.environ.get("SENDGRID_API_KEY")
