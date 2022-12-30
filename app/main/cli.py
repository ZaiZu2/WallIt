from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
import asyncio
import httpx
from httpx._exceptions import HTTPError
from httpx import Response
from datetime import datetime
from dateutil.rrule import rrule, DAILY
import csv
import click
from operator import attrgetter
from collections import defaultdict
from pathlib import Path

from app import db
from app.models import ExchangeRate
from app.exceptions import FileError


class ExchangeRatesLoader:
    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db
        self.exchange_rates: list[ExchangeRate] = []
        self.currencies: list[str] = []

    def download_exchange_rates(self, start_date: datetime, end_date: datetime) -> None:
        if start_date > end_date:
            raise ValueError("Ending date can only be specified after starting date")

        self._get_currencies()
        asyncio.run(self._get_timeseries(start_date, end_date))

    def save_to_csv(self) -> None:
        """Save loaded exchange rates to a .csv file"""

        if not self.exchange_rates:
            print("There are no records to save")
            return

        with open(f"exchange_rates.csv", "w", newline="") as csv_file:
            fieldnames = ["date", *self.currencies]
            csv_writer = csv.DictWriter(
                csv_file, fieldnames=fieldnames, delimiter=",", extrasaction="ignore"
            )
            csv_writer.writeheader()

            csv_dict: dict[datetime, dict[str, float]] = defaultdict(dict)
            # Ensure that records are sorted so .csv file is written chronologically
            for exchange_rate in sorted(
                self.exchange_rates, key=attrgetter("date", "source")
            ):
                csv_dict[exchange_rate.date][exchange_rate.source] = exchange_rate.rate

            # Attach date to each row
            for date, rates in csv_dict.items():
                csv_writer.writerow({"Date": date.strftime("%Y-%m-%d"), **rates})

        print("Exchange rates successfully written to the .csv file")

    def save_to_db(self) -> None:
        """Save loaded exchange rates to the db"""
        db.session.add_all(self.exchange_rates)
        db.session.commit()

    def load_from_csv(self, path: Path) -> None:
        exchange_rates = []
        try:
            with open(path, "r", newline="") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    date = row.pop("Date")
                    _ = [
                        ExchangeRate(
                            date=datetime.strptime(date, "%Y-%m-%d"),
                            source=code,
                            rate=float(rate) if rate else None,
                        )
                        for code, rate in row.items()
                    ]
                    exchange_rates.extend(_)
        except (KeyError, IOError):
            raise FileError(
                "Error occured while parsing .csv file. File might be corrupted."
            )

        self.exchange_rates = exchange_rates

    def _get_currencies(self) -> None:
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

            currencies = list(json["response"]["fiats"].keys())
            print(f"Successfully downloaded available currencies")
        except HTTPError:
            print(f"Failed to download available currencies")

        if not currencies:
            raise ValueError("No currencies were downloaded")
        self.currencies = currencies

    async def _get_timeseries(self, start_date: datetime, end_date: datetime) -> None:
        """Asynchronously consume API to download exchange rates for a set period

        Args:
            start_date (datetime): starting day of the period
            end_date (datetime): ending day of the period (included)
        """

        urls = set()
        for date in rrule(freq=DAILY, dtstart=start_date, until=end_date):
            url = current_app.config["CURRENCYSCOOP_HISTORICAL_URL"].format(
                key=current_app.config["CURRENCYSCOOP_API_KEY"],
                target_currency="EUR",
                date=date.strftime("%Y-%m-%d"),
            )
            urls.add(url)
        print(f"Querying API to get exchange rates for {len(urls)} days")

        timeout = httpx.Timeout(None)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            tasks = (client.get(url) for url in urls)
            responses = await asyncio.gather(*tasks)

        exchange_rates = []
        failed: list[Response] = []
        for response in responses:
            try:
                response.raise_for_status()
                json = response.json()

                date = datetime.strptime(json["response"]["date"], "%Y-%m-%d")
                _ = [
                    ExchangeRate(date=date, source=code.upper(), rate=rate)
                    for code, rate in json["response"]["rates"].items()
                ]
                exchange_rates.extend(_)
                print(
                    f"Successfully downloaded exchange rates for {json['response']['date']}"
                )
            except HTTPError:
                failed = failed + [response]

        if failed:
            print(f"Failed to download exchange rates for {len(failed)} days")
        self.exchange_rates = exchange_rates


def register(app: Flask) -> None:
    @app.cli.group()
    def rates() -> None:
        """Commands for loading/downloading exchange rates"""
        pass

    @rates.command()
    @click.argument("start")
    @click.argument("end")
    def download(start: str, end: str | None = None) -> None:
        """Download exchange rates for a selected period from an external API and
        save them to the database or external .csv file

        Args:
            start (str): starting date in 'YYYY-MM-DD' format
            end (str | None, optional): ending date in 'YYYY-MM-DD' format.
            If not specified, just starting day is downloaded.
        """
        end = start if end is None else end
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            print("Dates should be specified in 'YYYY-MM-DD' format")
            return
        if start_date > end_date:
            print("Ending date can only be specified after starting date")
            return

        rates_loader = ExchangeRatesLoader(db)
        rates_loader.download_exchange_rates(start_date, end_date)

        while True:
            confirm = input(
                "Would you like to save downloaded records to .csv file? (y/n) "
            )
            if confirm in ["Y", "y"]:
                rates_loader.save_to_csv()
                break
            elif confirm in ["N", "n"]:
                break
        while True:
            confirm = input(
                "Would you like to save downloaded records to database? (y/n) "
            )
            if confirm in ["Y", "y"]:
                rates_loader.save_to_db()
                break
            elif confirm in ["N", "n"]:
                break

    @rates.command()
    @click.argument("file")
    def load(file: str) -> None:
        """Load exchange rates from the .csv file and save them to the datebase

        Args:
            file (str): path to file
        """

        path = Path(file).resolve()
        if not path.exists():
            print("File '{path}' could not be found")
            return

        rates_loader = ExchangeRatesLoader(db)
        try:
            rates_loader.load_from_csv(path)
        except FileError as error:
            print(error.message)
            return
        rates_loader.save_to_db()
        print("Exchange rates successfully saved in the database")
