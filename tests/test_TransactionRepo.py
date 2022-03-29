#! python3
from importlib.resources import path
from re import A
import pytest, sys, pathlib, configparser

PROJECT_ROOT = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(PROJECT_ROOT))


from unittest.mock import patch
import FinanceApp.FinanceApp
from FinanceApp.FinanceApp import TransactionRepo, InvalidConfigError

#class TestTransactionRepoConstructor():


class TestEstablishConnection:
    def test_wrongConfigs(self, tmp_path: pathlib.Path):
        # Arrange
        wrongConfigPath: pathlib.Path = tmp_path.joinpath('wrongConfig.ini')
        wrongKeys: str = '''[postgresql]
                            wrongKey1=wrongValue1
                            wrongKey2=wrongValue2
                            wrongKey3=wrongValue3
                            wrongKey4=wrongValue4
                            wrongKey5=wrongValue5'''
        wrongConfig = configparser.ConfigParser()
        wrongConfig.read_string(wrongKeys)
        with open(wrongConfigPath, 'w') as configFile:
            wrongConfig.write(configFile)

        emptyConfigPath = tmp_path.joinpath('emptyConfig.ini')
        emptyKeys: str = ''
        emptyConfig = configparser.ConfigParser()
        emptyConfig.read_string(emptyKeys)
        with open(emptyConfigPath, 'w') as configFile:
            emptyConfig.write(configFile)

        wrongConfigs = (wrongConfigPath, emptyConfigPath)

        # Assert
        with patch('FinanceApp.FinanceApp.pathlib.Path.joinpath', side_effect=wrongConfigs):
            with pytest.raises(InvalidConfigError):
                # Act
                with TransactionRepo.establishConnection() as repo:
                    pass
            with pytest.raises(InvalidConfigError):
                # Act
                with TransactionRepo.establishConnection() as repo:
                    pass








wrongKeys: dict = {'postgresql': {'wrongKey1': 'wrongValue1',
                                        'wrongKey2': 'wrongValue2',
                                        'wrongKey3': 'wrongValue3',
                                        'wrongKey4': 'wrongValue4',
                                        'wrongKey5': 'wrongValue5'}
}
wrongConfig = configparser.ConfigParser()
wrongConfig.read_dict(wrongKeys)

emptyKeys: dict = {}

emptyConfig = configparser.ConfigParser()
emptyConfig.read_dict(emptyKeys)


@patch('FinanceApp.FinanceApp.configparser.ConfigParser', return_value=wrongConfig)
def test_wrongConfigs(config):
    with pytest.raises(Exception):
        with TransactionRepo.establishConnection() as repo:
            pass

                
'''    @patch('FinanceApp.FinanceApp.configparser.ConfigParser.__getitem__', return_value=wrongKeysConfig)
    def test_wrongKeysConfig(self, config):
        with pytest.raises(Exception):
            with TransactionRepo.establishConnection() as repo:
                pass
'''
poopConfig: dict = {}

@patch('FinanceApp.FinanceApp.configparser.ConfigParser', return_value=emptyConfig)
def test_emptyConfig(config):
    with pytest.raises(Exception):
        with TransactionRepo.establishConnection() as repo:
            pass


'''    @patch.object(FinanceApp.FinanceApp.configparser.ConfigParser, '__getitem__', side_effect=postgresConfig)
    def test_mock2(self, parsedConfig):
        
        with pytest.raises(Exception):
            with TransactionRepo.establishConnection() as repo:
                pass'''






# Arrange
@pytest.fixture()
def establishConnection() -> FinanceApp.FinanceApp.TransactionRepo:
    """Generate a new TransactionRepo instance with contextManager

    Returns:
        TransactionRepo: 
    """

    with FinanceApp.FinanceApp.TransactionRepo.establishConnection() as repo:
        return repo

def test_TableMapCaseSensitivity(establishConnection: FinanceApp.FinanceApp.TransactionRepo) -> None:
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

def test_TableMapIsEmpty(establishConnection: FinanceApp.FinanceApp.TransactionRepo) -> None:
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