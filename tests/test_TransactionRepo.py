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

# TODO: Methods called in TransactionRepo __init__ are called again with mocked config files in subsequent test cases
@pytest.fixture()
def instantiateRepo():
    with (
        patch("FinanceApp.FinanceApp.psycopg2.connect"),
        patch("FinanceApp.FinanceApp.psycopg2.extensions.register_type"),
    ):
        with TransactionRepo.establishConnection() as repo:
            return repo

class TestRepoInstantiation:
    """Test TransactionRepo's __init__ method and methods called within it"""

    @pytest.fixture
    def createTempConfigFile(self, tmp_path: pathlib.Path, request) -> pathlib.Path:
        """Create a temporary .ini file containing mock values used for tests

        Args:
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
            request (_type_): pytest object used for parametrizing fixtures

        Returns:
            pathlib.Path: path to a newly created .ini file
        """

        configPath = tmp_path.joinpath(request.param[0])
        configContent = request.param[1]
        config = CaseSensitiveConfigParser()
        config.read_string(configContent)
        with open(configPath, "w") as configFile:
            config.write(configFile)

        return configPath

    # Arrange
    @pytest.mark.parametrize(
        "createTempConfigFile",
        [
            (
                "wrongConfig.ini",
                """[postgresql]
                                wrongKey1=wrongValue1
                                wrongKey2=wrongValue2
                                wrongKey3=wrongValue3
                                wrongKey4=wrongValue4
                                wrongKey5=wrongValue5""",
            ),
            ("emptyConfig.ini", ""),
        ],
        indirect=True,
    )
    def test_establishConnection(self, createTempConfigFile: pathlib.Path) -> None:
        with patch(
            "FinanceApp.FinanceApp.pathlib.Path.joinpath",
            return_value=createTempConfigFile,
        ):
            # Assert
            with pytest.raises(InvalidConfigError):
                # Act
                with TransactionRepo.establishConnection() as repo:
                    pass

    # Arrange
    @pytest.mark.parametrize(
        "createTempConfigFile",
        [
            (
                "wrongPostgresMaps.ini",
                """[transactions]
                                        transactionId = id
                                        srcAmount = val__val
                                        srcCurrency = _val
                                        date = val_
                                        place = VAL

                                        [banks]
                                        bankId = id

                                        [users]
                                        userId = id""",
            ),
            ("emptyTableMaps.ini", ""),
        ],
        indirect=True,
    )
    def test_incorrectTableMaps(
        self, instantiateRepo: TransactionRepo, createTempConfigFile: pathlib.Path
    ) -> None:
        """Check behaviour when TableMaps config file has incorrect postgres table mappings

        Args:
            instantiateRepo (TransactionRepo): instance of TransactionRepo used for test
            createTempConfigFile (pathlib.Path): path to a newly created .ini file
        """

        with patch(
            "FinanceApp.FinanceApp.pathlib.Path.joinpath",
            return_value=createTempConfigFile,
        ):
            # Assert
            with pytest.raises(InvalidConfigError):
                # Act
                instantiateRepo._loadTableMaps()

    # Arrange
    @pytest.mark.parametrize(
        "createTempConfigFile",
        [
            (
                "correctPostgresMaps.ini",
                """[transactions]
                                        transactionId = id
                                        name = val_a
                                        title = title
                                        amount = amount
                                        currency = currency
                                        srcAmount = val_b
                                        srcCurrency = src_currency
                                        date = transaction_date
                                        place = place
                                        category = category
                                        userId = user_id
                                        bankId = bank_id

                                        [users]
                                        userId = id
                                        username = username
                                        password = val_c
                                        firstName = first_name
                                        lastName = val_d

                                        [banks]
                                        bankId = id
                                        bankName = bank_name""",
            )
        ],
        indirect=True,
    )
    def test_correctTableMaps(
        self, instantiateRepo: TransactionRepo, createTempConfigFile: pathlib.Path
    ) -> None:
        """Check if values are imported correctly from config file

        Args:
            instantiateRepo (TransactionRepo): instance of TransactionRepo used for test
            createTempConfigFile (pathlib.Path): path to a newly created .ini file
        """

        # Act
        with patch(
            "FinanceApp.FinanceApp.pathlib.Path.joinpath",
            return_value=createTempConfigFile,
        ):
            tableMaps = instantiateRepo._loadTableMaps()
            print("a")
            # Assert
            assert tableMaps["transactions"][0] == "transactions"
            assert tableMaps["transactions"][1]["name"] == "val_a"
            assert tableMaps["transactions"][1]["srcAmount"] == "val_b"

            assert tableMaps["users"][0] == "users"
            assert tableMaps["users"][1]["password"] == "val_c"
            assert tableMaps["users"][1]["lastName"] == "val_d"

    # Not much to unit test, a pure QUERY method 
    def test_parseBankId(self, instantiateRepo):
        pass