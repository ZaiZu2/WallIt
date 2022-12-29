from flask import Flask
import click
from pathlib import Path
import csv

def register(app: Flask) -> None:

    @app.cli.command()
    @click.argument('path')
    def currency(path: str) -> None:
        try:
            file = Path(path)
        except:
            raise 
        click.echo(file)