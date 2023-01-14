from datetime import datetime
from pathlib import Path

import click
from flask import Flask

from app import db
from app.exceptions import FileError
from app.external.exchange_rates import ExchangeRatesLoader


def register(app: Flask) -> None:
    @app.cli.group()
    def rates() -> None:
        """Commands for loading/downloading exchange rates"""
        pass

    @rates.command()
    @click.argument("start")
    @click.argument("end", required=False)
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
        if (
            start_date > end_date
            and start_date < datetime.now()
            and end_date < datetime.now()
        ):
            print("Ending date can only be specified after starting date")
            return

        ExchangeRatesLoader.download_exchange_rates(start_date, end_date)

        while True:
            confirm = input(
                "Would you like to save downloaded records to .csv file? (y/n) "
            )
            if confirm in ["Y", "y"]:
                ExchangeRatesLoader.save_to_csv()
                break
            elif confirm in ["N", "n"]:
                break
        while True:
            confirm = input(
                "Would you like to save downloaded records to database? (y/n) "
            )
            if confirm in ["Y", "y"]:
                ExchangeRatesLoader.save_to_db()
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

        try:
            ExchangeRatesLoader.load_from_csv(path)
        except FileError as error:
            print(error.message)
            return
        ExchangeRatesLoader.save_to_db()
