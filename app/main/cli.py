from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import asyncio
import httpx
from httpx import Response
from datetime import datetime
from dateutil.rrule import rrule, DAILY
import csv
import click

from app import db

class ExchangeRatesLoader:
    
    def __init__(self, db: SQLAlchemy) -> None:
        self.db = db
        self.exchange_rates = {}
        self.currencies: list[str] = []

    def _get_currencies(self) -> None:
        currency_url = "https://api.currencybeacon.com/v1/currencies?api_key=39c83a7c50bb795501ee384a76c18cac"

        try:
            response = httpx.get(currency_url)
            response.raise_for_status()
            json = response.json()
            if json["meta"]["code"] != 200:
                raise Exception

            currencies = list(json["response"]["fiats"].keys())
            print(f"Successfully downloaded available currencies")
        except Exception:
            print(f"Failed to download available currencies")
            raise Exception()

        if not currencies:
            raise Exception
        self.currencies = currencies

    async def _get_timeseries(self, start_date: datetime, end_date: datetime) -> None:
        scoop_url = "https://api.currencyscoop.com/v1/historical?api_key=39c83a7c50bb795501ee384a76c18cac&base=EUR&date={date}"
        urls = set()
        for date in rrule(freq=DAILY, dtstart=start_date, until=end_date):
            urls.add(scoop_url.format(date=date.strftime("%Y-%m-%d")))
        print(f"Querying API to get exchange rates for {len(urls)} days")

        timeout = httpx.Timeout(None)
        limits = httpx.Limits(max_keepalive_connections=20, max_connections=100)
        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            tasks = (client.get(url) for url in urls)
            responses = await asyncio.gather(*tasks)

        exchange_rates = {}
        failed: list[Response] = []
        for response in responses:
            try:
                response.raise_for_status()
                json = response.json()
                if json["meta"]["code"] != 200:
                    raise Exception

                # date_obj = datetime().strptime(json['response']['date'], "%Y-%m-%d")
                exchange_rates[json["response"]["date"]] = json["response"]["rates"]
                print(
                    f"Successfully downloaded exchange rates for {json['response']['date']}"
                )
            except:
                failed = failed + [response]

        if failed:
            print(f"Failed to download exchange rates for {len(failed)} days")
        self.exchange_rates = exchange_rates

    def download_exchange_rates(self, start_date: datetime, end_date: datetime):
        self._get_currencies()
        asyncio.run(self._get_timeseries(start_date, end_date))

    def save_to_csv(self):
        """Save loaded exchange rates to a .csv file"""

        sorted_rates = sorted(self.exchange_rates.items())
        with open(
            f'exchange_rates_{sorted_rates[0][0].strftime("%Y-%m-%d")}_{sorted_rates[-1][0].strftime("%Y-%m-%d")}.csv',
            "w",
            newline="",
        ) as f:
            fieldnames = ["Date", *self.currencies]
            csv_writer = csv.DictWriter(
                f, fieldnames=fieldnames, delimiter=",", extrasaction="ignore"
            )
            csv_writer.writeheader()
            for date, record in sorted_rates:
                csv_writer.writerow({"Date": date, **record})
        print("Exchange rates successfully written to the .csv file")


def register(app: Flask) -> None:
    @app.cli.group()
    def rates() -> None:
        """Commands for loading/downloading exchange rates"""
        pass

    @rates.command()
    @click.argument("start")
    @click.argument("end")
    def download(start: str, end: str | None = None) -> None:
        end = start if end is None else end
        start_date = datetime.strptime(start, "%Y-%m-%d")
        end_date = datetime.strptime(end, "%Y-%m-%d")
        if start_date > end_date:
            raise Exception

        rates_loader = ExchangeRatesLoader(db)
        rates_loader.download_exchange_rates(start_date, end_date)

