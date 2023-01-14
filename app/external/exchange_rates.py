import asyncio
import csv
from collections import defaultdict
from datetime import datetime
from operator import attrgetter
from pathlib import Path

import httpx
from dateutil.rrule import DAILY, rrule
from flask import current_app
from httpx import Response
from httpx._exceptions import HTTPError

from app import cache, db
from app.exceptions import ExternalApiError, FileError
from app.external.schemas import ExchangeRateSchema
from app.models import ExchangeRate


class ExchangeRatesLoader:
    db = db
    exchange_rates: list[ExchangeRateSchema] = []
    currencies: set[str]

    @classmethod
    def download_exchange_rates(cls, start_date: datetime, end_date: datetime) -> None:
        if start_date > end_date:
            raise ValueError("Ending date can only be specified after starting date")

        cls.get_currencies()
        asyncio.run(cls._get_timeseries(start_date, end_date))

    @classmethod
    def save_to_csv(cls) -> None:
        """Save loaded exchange rates to a .csv file"""

        if not cls.exchange_rates:
            print("There are no records to save")
            return

        # Ensure that records are sorted so .csv file is written chronologically
        sorted_rates = sorted(cls.exchange_rates, key=attrgetter("date", "source"))
        file_name = f"exchange_rates_{sorted_rates[0].date.strftime('%Y-%m-%d')}_{sorted_rates[-1].date.strftime('%Y-%m-%d')}.csv"
        with open(file_name, "w", newline="") as csv_file:
            fieldnames = ["date", *current_app.config["SUPPORTED_CURRENCIES"]]
            csv_writer = csv.DictWriter(
                csv_file, fieldnames=fieldnames, delimiter=",", extrasaction="ignore"
            )
            csv_writer.writeheader()

            csv_dict: dict[datetime, dict[str, float]] = defaultdict(dict)
            for exchange_rate in sorted_rates:
                csv_dict[exchange_rate.date][exchange_rate.source] = exchange_rate.rate

            # Attach date to each row
            for date, rates in csv_dict.items():
                csv_writer.writerow({"date": date.strftime("%Y-%m-%d"), **rates})

        print("Exchange rates successfully written to the .csv file")

    @classmethod
    def save_to_db(cls) -> None:
        """Save loaded exchange rates to the db"""
        db.session.add_all(cls.exchange_rates)
        db.session.commit()
        print("Exchange rates successfully written to the db")

    @classmethod
    def load_from_csv(cls, path: Path) -> None:
        """Load exchange rates from a .csv file

        Args:
            path (Path): path to file

        Raises:
            FileError: raised in case of failed parsing
        """
        exchange_rates = []
        schema = ExchangeRateSchema()
        try:
            with open(path, "r", newline="") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    date = row.pop("date")
                    for code, rate in row.items():
                        verified_data = schema.load(
                            dict(date=date, source=code, rate=rate)
                        )
                        exchange_rates.append(ExchangeRate(**verified_data))
        except (KeyError, IOError):
            raise FileError(
                "Error occured while parsing .csv file. File might be corrupted.",
            )

        cls.exchange_rates = exchange_rates

    @classmethod
    @cache.cached(key_prefix="currencies")
    def get_currencies(cls) -> set[str]:
        """Consume API to download currencies for which exchange rates are available

        Raises:
            ValueError: No currencies were downloaded, altho API call was successful
        """
        url: str = current_app.config["CURRENCYSCOOP_CURRENCIES_URL"].format(
            key=current_app.config["CURRENCYSCOOP_API_KEY"]
        )

        try:
            response = httpx.get(url)
            response.raise_for_status()
            json = response.json()

            currencies = set(json["response"]["fiats"].keys())
        except HTTPError as error:
            raise ExternalApiError(
                "Failed to download available currencies: " + error.args[0]
            )

        print(f"Successfully downloaded available currencies")
        if subset := current_app.config["SUPPORTED_CURRENCIES"] - currencies:
            print(
                f"Exchange rates are not available for following supported currencies: {subset}"
            )
            currencies = currencies.intersection(
                current_app.config["SUPPORTED_CURRENCIES"]
            )

        if not currencies:
            raise ValueError(
                "No currencies were downloaded or are available to download"
            )
        cls.currencies = currencies
        return currencies

    @classmethod
    async def _get_timeseries(cls, start_date: datetime, end_date: datetime) -> None:
        """Asynchronously consume API to download exchange rates for a set period

        Args:
            start_date (datetime): starting day of the period
            end_date (datetime): ending day of the period (included)
        """

        urls = set()
        for date in rrule(freq=DAILY, dtstart=start_date, until=end_date):
            url = current_app.config["CURRENCYSCOOP_HISTORICAL_URL"].format(
                key=current_app.config["CURRENCYSCOOP_API_KEY"],
                date=date.strftime("%Y-%m-%d"),
                symbols=",".join(current_app.config["SUPPORTED_CURRENCIES"]),
            )
            urls.add(url)
        print(f"Querying API to get exchange rates for {len(urls)} days")

        timeout = httpx.Timeout(None)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            tasks = (client.get(url) for url in urls)
            responses = await asyncio.gather(*tasks)

        schema = ExchangeRateSchema()
        exchange_rates = []
        failed: list[Response] = []
        for response in responses:
            try:
                response.raise_for_status()
                json = response.json()

                for code, rate in json["response"]["rates"].items():
                    verified_data = schema.load(
                        dict(date=json["response"]["date"], source=code, rate=rate)
                    )
                    exchange_rates.append(ExchangeRate(**verified_data))
                print(
                    f"Successfully downloaded exchange rates for {json['response']['date']}"
                )
            except HTTPError:
                failed = failed + [response]

        if failed:
            print(f"Failed to download exchange rates for {len(failed)} days")
        cls.exchange_rates = exchange_rates
