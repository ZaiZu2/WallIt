#! python3

import pytest, sys, pathlib, pytest_mock, mock

PROJECT_ROOT = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(PROJECT_ROOT))
import FinanceApp.FinanceApp
from FinanceApp.FinanceApp import TransactionRepo


# Arrange
@pytest.fixture()
@mock.patch("FinanceApp.FinanceApp.psycopg2.connect")
def mockConnection(mockConnect) -> TransactionRepo:
    """Generate a new TransactionRepo instance with contextManager

    Returns:
        TransactionRepo: 
    """

    mockConn = mockConnect.return_value
    mockCur = mockConn.cursor.return_value

    with TransactionRepo.establishConnection() as repo:
        return repo

# Arrange
@pytest.fixture()
def establishConnection() -> TransactionRepo:
    """Generate a new TransactionRepo instance with contextManager

    Returns:
        TransactionRepo: 
    """

    with TransactionRepo.establishConnection() as repo:
        return repo

def test_TableMapCaseSensitivity(establishConnection: TransactionRepo) -> None:
    """Check if loaded table column maps are case-sensitive (important as the source code uses camelCase)

    Args:
        establishConnection (TransactionRepo): 
    """

    # Act
    isUppercase = False
    tableDict = establishConnection.tableMaps # Dict with loaded tables

    for table in tableDict.values():
        for columnName in table[1].keys():
            [isUppercase := True if letter.isupper() else isUppercase for letter in columnName]
            if isUppercase == True: break # Break the inner loop
        else:
            continue # Continue if the inner loop wasn't broken
        break # Inner loop was broken, break the outer

    # Assert 
    assert isUppercase is True

def test_TableMapIsEmpty(establishConnection: TransactionRepo) -> None:
    """Check if loaded table column maps were loaded, and are not empty

    Args:
        establishConnection (TransactionRepo): 
    """

    # Act
    isEmpty = False
    tableDict = establishConnection.tableMaps # Dict with loaded tables

    for table in tableDict.values():
        if not table[1]:
            isEmpty = True
            break

    # Assert 
    assert isEmpty is False

# _parkBankId testing

def test_bankIdMapIsEmpty():
    # Check if queried map is not empty
    pass

def test_bankIdMapCorrectTypes():
    # Check if variable is dict[str, int]
    pass