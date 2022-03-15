#! python3

from curses.ascii import isupper
import pytest, sys, pathlib

PROJECT_ROOT = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(PROJECT_ROOT))
from FinanceApp.FinanceApp import TransactionRepo

#Arrange
@pytest.fixture(autouse=True)
def createTransactionRepo():
    return TransactionRepo()

def test_databaseConfigCaseSensitive():
    #Act
    postgresConfig, userMap, transactionMap = createTransactionRepo()._readDatabaseConfig()

    [isUpper := str(key).isupper() for key, value in postgresConfig if repr(key).isupper() or repr(key).isupper()]

    #Assert
    assert 

def test_postgresConfigExists():
    pass

def test_transactionTableConfigExists():
    pass

def test_userTableConfigExists():
    pass