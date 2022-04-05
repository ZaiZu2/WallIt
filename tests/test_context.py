#! python3
from unittest import mock
import pytest, sys, pathlib

PROJECT_ROOT = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(PROJECT_ROOT))

from unittest.mock import patch
import FinanceApp.FinanceApp
from FinanceApp.FinanceApp import (
    TransactionRepo,
    InvalidConfigError,
    CaseSensitiveConfigParser,
)


@pytest.fixture()
def instantiateRepo():
    with (
        patch("FinanceApp.FinanceApp.psycopg2.connect"),
        patch("FinanceApp.FinanceApp.psycopg2.extensions.register_type"),
    ):
        with TransactionRepo.establishConnection() as repo:
            return repo


def test_repo(instantiateRepo):
    repo = instantiateRepo
    print("a")
