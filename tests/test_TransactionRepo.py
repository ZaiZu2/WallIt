#! python3
import py
import pytest, sys, pathlib, csv
from datetime import datetime

PROJECT_ROOT = pathlib.Path(__file__).parents[1].resolve()
sys.path.append(str(PROJECT_ROOT))

from unittest.mock import patch
import FinanceApp.FinanceApp
from FinanceApp.FinanceApp import (
    TransactionRepo,
    Transaction,
    User,
    InvalidConfigError,
    LoginFailedError,
    FileError,
)

from FinanceApp.FinanceApp import fileOpen

# Methods called in TransactionRepo __init__ (during this fixture) are redundant.
# They called again with mocked config files in subsequent test cases
@pytest.fixture()
def instantiateRepo():
    with (
        patch("FinanceApp.FinanceApp.psycopg2.connect"),
        patch("FinanceApp.FinanceApp.psycopg2.extensions.register_type"),
        patch(
            "FinanceApp.FinanceApp.TransactionRepo._parseBankId",
            return_value={"Equabank": 1, "Revolut": 2},
        ),
    ):
        with TransactionRepo.establishConnection() as repo:
            return repo


@pytest.fixture()
def createUser():
    return User("1", "ZaiZu", "passcode", "John", "Smith")


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
        configPath.write_text(configContent, encoding="utf8")

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
                   name = val_a
                   srcAmount = val_b

                   [users]
                   password = val_c
                   lastName = val_d

                   [banks]""",
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

            # Assert
            assert tableMaps["transactions"][0] == "transactions"
            assert tableMaps["transactions"][1]["name"] == "val_a"
            assert tableMaps["transactions"][1]["srcAmount"] == "val_b"

            assert tableMaps["users"][0] == "users"
            assert tableMaps["users"][1]["password"] == "val_c"
            assert tableMaps["users"][1]["lastName"] == "val_d"


class TestQueryProcessing:
    """Test methods responsible for querying and postprocessing queries"""

    def test_parseBankId(self, instantiateRepo: TransactionRepo) -> None:
        """Check if query return values are correctly cast to dict

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
        """

        # Arrange
        expected = instantiateRepo.cur.fetchall.return_value = [
            ("Equabank", 1),
            ("Revolut", 2),
            ("CityBank", 3),
        ]

        # Act
        bankMap = instantiateRepo._parseBankId()

        # Assert
        for i, (bankName, bankId) in enumerate(bankMap.items()):
            assert isinstance(bankName, str)
            assert isinstance(bankId, int)

            # Check if 'expected' values are same as values cast to dict
            assert bankName == expected[i][0]
            assert bankId == expected[i][1]

    def test_successfulUserQuery(self, instantiateRepo: TransactionRepo) -> None:
        """Check if query return values are correctly cast to User class instance

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
        """

        # Arrange
        expected = instantiateRepo.cur.fetchone.return_value = (
            1,
            "ZaiZu",
            "password",
            "John",
            "Smith",
        )

        # Act
        user = instantiateRepo.userQuery(expected[1])

        # Assert
        assert isinstance(user.userId, int)
        assert user.userId == expected[0]
        assert isinstance(user.username, str)
        assert user.username == expected[1]
        assert isinstance(user.password, str)
        assert user.password == expected[2]
        assert isinstance(user.firstName, str)
        assert user.firstName == expected[3]
        assert isinstance(user.lastName, str)
        assert user.lastName == expected[4]

    def test_emptyUserQuery(self, instantiateRepo: TransactionRepo) -> None:
        """Check if query return values are correctly cast to User class instance

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
        """

        # Arrange
        expected = instantiateRepo.cur.fetchone.return_value = ()

        # Assert
        with pytest.raises(LoginFailedError):
            # Act
            user = instantiateRepo.userQuery("wrongUsername")


class TestStatementImports:
    """Test methods used for importing statements from various banks"""

    def createRevolutStatement(
        self, dirPath: pathlib.Path, fileName: str, content: tuple[str, ...]
    ) -> pathlib.Path:
        """Create a temporary .csv Revolut statement used for tests

        Args:
            dirPath (pathlib.Path): path to temporary file location
            fileName (str):
            content (tuple[str, ...]): tuple with .csv rows

        Returns:
            pathlib.Path: path to a newly created .ini file
        """

        statementPath = dirPath.joinpath(fileName)
        with open(statementPath, "w", newline="\n") as statement:
            for row in content:
                statement.write(row + "\n")

        return statementPath

    def test_RevolutCorrectImport(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test import process behaviour when provided with correct input files

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """

        # Arrange
        files = (
            (
                "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance",
                "EXCHANGE,Current,2020-11-06 16:51:47,2020-11-06 16:51:47,Exchanged to EUR,90.00,0.00,EUR,COMPLETED,90.00",
                "CARD_PAYMENT,Current,2020-11-10 22:39:13,2020-11-14 01:43:47,amazon.de,-85.26,0.00,EUR,COMPLETED,4.74",
            ),
            (
                "Type,Product,Started Date,Completed Date,Description,Amount,Fee,Currency,State,Balance",
                "EXCHANGE,Current,2021-01-02 07:39:54,2021-01-02 07:39:54,Exchanged to PLN,-200.00,0.00,CZK,COMPLETED,93.17",
                "TOPUP,Current,2021-02-12 08:27:03,2021-02-12 08:27:33,Top-Up by *6579,400.00,0.00,CZK,COMPLETED,493.17",
                "CARD_PAYMENT,Current,2021-02-12 08:27:54,2021-02-12 19:47:20,aliexpress.com,-171.67,0.00,CZK,COMPLETED,321.50",
            ),
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createRevolutStatement(
                    self, tmp_path, f"correctRevolutStatement{i}.csv", file
                )
            )

        results: list[Transaction] = []
        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Act
            results += instantiateRepo.loadRevolutStatement(createUser)

        # Assert
        assert results[2].name == "EXCHANGE"
        assert results[2].title == "Exchanged to PLN"
        assert isinstance(results[2].srcAmount, float)
        assert results[2].srcAmount == -200.00
        assert results[2].srcCurrency == "CZK"
        assert isinstance(results[2].date, datetime)
        assert results[2].date == datetime(2021, 1, 2, 7, 39, 54)
        assert results[2].bankId == instantiateRepo._bankMap["Revolut"]
        assert results[2].userId == createUser.userId

    def test_RevolutIncorrectImport(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test import process behaviour when provided with incorrect .csv file structure 
        (wrong header/columns)

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """


        # Arrange
        files = (
            (
                "WRONG,Product,Started Date,Completed Date,WRONG,WRONG,Fee,Currency,State,Balance",
                "EXCHANGE,Current,2020-11-06 16:51:47,2020-11-06 16:51:47,Exchanged to EUR,90.00,0.00,EUR,COMPLETED,90.00",
                "CARD_PAYMENT,Current,2020-11-10 22:39:13,2020-11-14 01:43:47,amazon.de,-85.26,0.00,EUR,COMPLETED,4.74",
            ),
            (
                "Type,Product,Started Date,WRONG,Description,Amount,Fee,WRONG,State,Balance",
                "EXCHANGE,Current,2021-01-02 07:39:54,2021-01-02 07:39:54,Exchanged to PLN,-200.00,0.00,CZK,COMPLETED,93.17",
                "TOPUP,Current,2021-02-12 08:27:03,2021-02-12 08:27:33,Top-Up by *6579,400.00,0.00,CZK,COMPLETED,493.17",
                "CARD_PAYMENT,Current,2021-02-12 08:27:54,2021-02-12 19:47:20,aliexpress.com,-171.67,0.00,CZK,COMPLETED,321.50",
            ),
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createRevolutStatement(
                    self, tmp_path, f"incorrectRevolutStatement{i}.csv", file
                )
            )

        results: list[Transaction] = []
        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Assert
            with pytest.raises(FileError):
                    # Act
                    results += instantiateRepo.loadRevolutStatement(createUser)

    def createEquabankStatement(
        self, dirPath: pathlib.Path, fileName: str, content: str) -> pathlib.Path:
        """Create a temporary .xml Equabank statement used for tests

        Args:
            dirPath (pathlib.Path): path to temporary file location
            fileName (str):
            content (tuple[str, ...]): tuple with .csv rows

        Returns:
            pathlib.Path: path to a newly created .ini file
        """

        statementPath = dirPath.joinpath(fileName)
        statementPath.write_text(content)

        return statementPath

    def test_EquabankCorrectImport(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test import process behavior when provided with correct input files

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """

        # TODO: .xml test files as strings listed below. 
        # Messy Jesus Christ. No clue how it should be done, 
        # I think it's not the scope of unittests, but better than no tests.
        
        # Arrange
        files = (
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>7</NbOfNtries>
                                <Sum>25</Sum>
                                <TtlNetNtry>
                                    <Amt>25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>3</NbOfNtries>
                                <Sum>55</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>4</NbOfNtries>
                                <Sum>30</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">10</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">10</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">5</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-11+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-11+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">5</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>ALBERT VAM DEKUJE</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">15</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">15</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>Billa Praha Blox</Nm>
                                            <PstlAdr>
                                                <TwnNm>Praha 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">25</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>CESKA SPORITELNA, A.S.</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                        <CdtrAcct>
                                            <Id>
                                                <Othr>
                                                    <Id>1011071271</Id>
                                                </Othr>
                                            </Id>
                                            <Nm>NOSTRO - CARD TRANSA</Nm>
                                        </CdtrAcct>
                                    </RltdPties>
                                    <RltdAgts>
                                        <CdtrAgt>
                                            <FinInstnId>
                                                <Nm>Equa bank a.s.</Nm>
                                                <Othr>
                                                    <Id>6100</Id>
                                                </Othr>
                                            </FinInstnId>
                                        </CdtrAgt>
                                    </RltdAgts>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>""",
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                                <TtlNetNtry>
                                    <Amt>11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>"""
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createEquabankStatement(
                    self, tmp_path, f"correctEquabankStatement{i}.xml", file
                )
            )

        results: list[Transaction] = []

        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Act
            results += instantiateRepo.loadEquabankStatement(createUser)        

        # Assert
        assert results[0].name == "TON KIN"
        assert results[0].title == None
        assert results[0].srcAmount == None
        assert results[0].srcCurrency == None

        assert results[1].amount == -5
        assert results[1].currency == 'CZK'        

        assert results[2].date == datetime(2020, 4, 13, 2, 0)
        assert results[2].bankId == instantiateRepo._bankMap["Equabank"]
        assert results[2].userId == createUser.userId

    def test_EquabankWrongSum(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test when statement has incorrectly stated Transaction amount sum

        Wrong parts:
        ...
        <TtlNetNtry>
            <Amt>0</Amt> (!= 25)
        ...
        <TtlNetNtry>
            <Amt>0</Amt> (!= 11.11)
        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """

        # TODO: .xml test files as strings listed below. 
        # Messy Jesus Christ. No clue how it should be done, 
        # I think it's not the scope of unittests, but better than no tests.
        
        # Arrange
        files = (
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>2</NbOfNtries>
                                <Sum>0</Sum>
                                <TtlNetNtry>
                                    <Amt>0</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>2</NbOfNtries>
                                <Sum>40</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">15</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">15</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>Billa Praha Blox</Nm>
                                            <PstlAdr>
                                                <TwnNm>Praha 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">25</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>CESKA SPORITELNA, A.S.</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                        <CdtrAcct>
                                            <Id>
                                                <Othr>
                                                    <Id>1011071271</Id>
                                                </Othr>
                                            </Id>
                                            <Nm>NOSTRO - CARD TRANSA</Nm>
                                        </CdtrAcct>
                                    </RltdPties>
                                    <RltdAgts>
                                        <CdtrAgt>
                                            <FinInstnId>
                                                <Nm>Equa bank a.s.</Nm>
                                                <Othr>
                                                    <Id>6100</Id>
                                                </Othr>
                                            </FinInstnId>
                                        </CdtrAgt>
                                    </RltdAgts>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>""",
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>0</Sum>
                                <TtlNetNtry>
                                    <Amt>0</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>"""
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createEquabankStatement(
                    self, tmp_path, f"incorrectEquabankStatement{i}.xml", file
                )
            )

        results: list[Transaction] = []

        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Assert
            with pytest.raises(FileError):
                # Act
                results += instantiateRepo.loadEquabankStatement(createUser)  
    
    def test_EquabankWrongFormat(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test when statement has completely wrong .xml formating

        Deleted '</BkToCstmrStmt>'

        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """

        # TODO: .xml test files as strings listed below. 
        # Messy Jesus Christ. No clue how it should be done, 
        # I think it's not the scope of unittests, but better than no tests.
        
        # Arrange
        files = (
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>2</NbOfNtries>
                                <Sum>0</Sum>
                                <TtlNetNtry>
                                    <Amt>0</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>2</NbOfNtries>
                                <Sum>40</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">15</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">15</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>Billa Praha Blox</Nm>
                                            <PstlAdr>
                                                <TwnNm>Praha 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">25</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>CESKA SPORITELNA, A.S.</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                        <CdtrAcct>
                                            <Id>
                                                <Othr>
                                                    <Id>1011071271</Id>
                                                </Othr>
                                            </Id>
                                            <Nm>NOSTRO - CARD TRANSA</Nm>
                                        </CdtrAcct>
                                    </RltdPties>
                                    <RltdAgts>
                                        <CdtrAgt>
                                            <FinInstnId>
                                                <Nm>Equa bank a.s.</Nm>
                                                <Othr>
                                                    <Id>6100</Id>
                                                </Othr>
                                            </FinInstnId>
                                        </CdtrAgt>
                                    </RltdAgts>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>""",
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>0</Sum>
                                <TtlNetNtry>
                                    <Amt>0</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>"""
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createEquabankStatement(
                    self, tmp_path, f"incorrectEquabankStatement{i}.xml", file
                )
            )

        results: list[Transaction] = []

        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Assert
            with pytest.raises(FileError):
                # Act
                results += instantiateRepo.loadEquabankStatement(createUser)  

    def test_EquabankWrongValues(
        self, instantiateRepo: TransactionRepo, createUser: User, tmp_path: pathlib.Path
    ) -> None:
        """Test import process behavior when provided with correct input files
            
            Wrong parts:
            ...
            <Amt Ccy="CZK">10WRONG</Amt>
            ...
            <BookgDt>
                <Dt>WRONG</Dt>
            ...
        
        Args:
            instantiateRepo (TransactionRepo): fixture instantiating repo
            createUser (User): fixture instantiating user
            tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
        """

        # TODO: .xml test files as strings listed below. 
        # Messy Jesus Christ. No clue how it should be done, 
        # I think it's not the scope of unittests, but better than no tests.
        
        # Arrange
        files = (
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">323.32</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>7</NbOfNtries>
                                <Sum>25</Sum>
                                <TtlNetNtry>
                                    <Amt>25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>3</NbOfNtries>
                                <Sum>55</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>4</NbOfNtries>
                                <Sum>30</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">10</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">10WRONG</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">5</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-11+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-11+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">5</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>ALBERT VAM DEKUJE</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">15</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-13+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">15</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>Billa Praha Blox</Nm>
                                            <PstlAdr>
                                                <TwnNm>Praha 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                        <Ntry>
                            <Amt Ccy="CZK">25</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-16+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">25</Amt>
                                    <CdtDbtInd>CRDT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>CESKA SPORITELNA, A.S.</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                        <CdtrAcct>
                                            <Id>
                                                <Othr>
                                                    <Id>1011071271</Id>
                                                </Othr>
                                            </Id>
                                            <Nm>NOSTRO - CARD TRANSA</Nm>
                                        </CdtrAcct>
                                    </RltdPties>
                                    <RltdAgts>
                                        <CdtrAgt>
                                            <FinInstnId>
                                                <Nm>Equa bank a.s.</Nm>
                                                <Othr>
                                                    <Id>6100</Id>
                                                </Othr>
                                            </FinInstnId>
                                        </CdtrAgt>
                                    </RltdAgts>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>""",
            """<?xml version='1.0' encoding='UTF-8'?>
            <Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.06">
                <BkToCstmrStmt>
                    <GrpHdr>
                        <MsgId>camt.053-2020-04-30-4</MsgId>
                        <CreDtTm>2021-12-25T13:00:36.705+01:00</CreDtTm>
                        <MsgRcpt>
                            <Nm>John Smith</Nm>
                            <PstlAdr>
                                <StrtNm>Pork street</StrtNm>
                                <BldgNb>582</BldgNb>
                                <PstCd>1200</PstCd>
                                <TwnNm>Praha</TwnNm>
                                <Ctry>Zimbabwe</Ctry>
                            </PstlAdr>
                        </MsgRcpt>
                    </GrpHdr>
                    <Stmt>
                        <Id>CZ7461000003423429823417-2020-04-30</Id>
                        <ElctrncSeqNb>4</ElctrncSeqNb>
                        <LglSeqNb>4</LglSeqNb>
                        <CreDtTm>2020-04-30T00:00:00.000+02:00</CreDtTm>
                        <FrToDt>
                            <FrDtTm>2020-04-01T00:00:00.000+02:00</FrDtTm>
                            <ToDtTm>2020-04-30T00:00:00.000+02:00</ToDtTm>
                        </FrToDt>
                        <Acct>
                            <Id>
                                <IBAN>CZ7213000000001029236436</IBAN>
                            </Id>
                            <Ccy>CZK</Ccy>
                            <Ownr>
                                <Nm>John Smith</Nm>
                                <PstlAdr>
                                    <StrtNm>Pork street</StrtNm>
                                    <BldgNb>582</BldgNb>
                                    <PstCd>1200</PstCd>
                                    <TwnNm>Praha</TwnNm>
                                    <Ctry>Zimbabwe</Ctry>
                                </PstlAdr>
                            </Ownr>
                            <Svcr>
                                <FinInstnId>
                                    <BICFI>EQBKCZPP</BICFI>
                                    <Nm>Equa bank a.s.</Nm>
                                    <Othr>
                                        <Id>6100</Id>
                                    </Othr>
                                </FinInstnId>
                            </Svcr>
                        </Acct>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>PRCD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-01+02:00</Dt>
                            </Dt>
                        </Bal>
                        <Bal>
                            <Tp>
                                <CdOrPrtry>
                                    <Cd>CLBD</Cd>
                                </CdOrPrtry>
                            </Tp>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>CRDT</CdtDbtInd>
                            <Dt>
                                <Dt>2020-04-30+02:00</Dt>
                            </Dt>
                        </Bal>
                        <TxsSummry>
                            <TtlNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                                <TtlNetNtry>
                                    <Amt>11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                </TtlNetNtry>
                            </TtlNtries>
                            <TtlCdtNtries>
                                <NbOfNtries>0</NbOfNtries>
                                <Sum>0</Sum>
                            </TtlCdtNtries>
                            <TtlDbtNtries>
                                <NbOfNtries>1</NbOfNtries>
                                <Sum>11.11</Sum>
                            </TtlDbtNtries>
                        </TxsSummry>
                        <Ntry>
                            <Amt Ccy="CZK">11.11</Amt>
                            <CdtDbtInd>DBIT</CdtDbtInd>
                            <Sts>BOOK</Sts>
                            <BookgDt>
                                <Dt>WRONG</Dt>
                            </BookgDt>
                            <ValDt>
                                <Dt>2020-04-10+02:00</Dt>
                            </ValDt>
                            <BkTxCd>
                                <Prtry>
                                    <Cd>555</Cd>
                                </Prtry>
                            </BkTxCd>
                            <NtryDtls>
                                <TxDtls>
                                    <Refs>
                                        <ChqNb>************6579</ChqNb>
                                    </Refs>
                                    <Amt Ccy="CZK">11.11</Amt>
                                    <CdtDbtInd>DBIT</CdtDbtInd>
                                    <RltdPties>
                                        <Cdtr>
                                            <Nm>TON KIN</Nm>
                                            <PstlAdr>
                                                <TwnNm>PRAHA 6</TwnNm>
                                            </PstlAdr>
                                        </Cdtr>
                                    </RltdPties>
                                </TxDtls>
                            </NtryDtls>
                        </Ntry>
                    </Stmt>
                </BkToCstmrStmt>
            </Document>"""
        )

        filePaths: list[pathlib.Path] = []
        for i, file in enumerate(files):
            filePaths.append(
                TestStatementImports.createEquabankStatement(
                    self, tmp_path, f"correctEquabankStatement{i}.xml", file
                )
            )

        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=filePaths,
        ):
            # Assert
            with pytest.raises(FileError): 
                # Act
                results = instantiateRepo.loadEquabankStatement(createUser)        


def test_fileOpenAllIncorrect(tmp_path: pathlib.Path) -> None:
    """Test file handling while all file formats are incorrect

    Args:
        tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
    """

    # Arrange
    suffixes = [".xml", ".csv", ".pdf"]
    filePaths: list[pathlib.Path] = []
    for i, suffix in enumerate(suffixes):
        filePaths.append(tmp_path.joinpath(f"file{i}{suffix}"))
        with open(filePaths[i], "w") as file:
            file.write(f"{i}")

    strFilePaths = [str(filePath) for filePath in filePaths]

    # Act
    with pytest.raises(FileError):
        with patch(
            "tkinter.filedialog.askopenfilenames",
            return_value=strFilePaths,
        ):
            returnPaths = fileOpen(".txt")


def test_fileOpenSomeIncorrect(tmp_path: pathlib.Path) -> None:
    """Test file handling while some file formats are incorrect

    Args:
        tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
    """

    # Arrange
    suffixes = [".txt", ".csv", ".pdf"]
    filePaths: list[pathlib.Path] = []
    for i, suffix in enumerate(suffixes):
        filePaths.append(tmp_path.joinpath(f"file{i}{suffix}"))
        with open(filePaths[i], "w") as file:
            file.write(f"{i}")

    strFilePaths = [str(filePath) for filePath in filePaths]

    # Act
    with patch(
        "tkinter.filedialog.askopenfilenames",
        return_value=strFilePaths,
    ):
        returnPaths = fileOpen(".txt")

    # Assert
    assert len(returnPaths) == 1
    assert returnPaths[0].suffix == ".txt"


def test_fileOpenAllCorrect(tmp_path: pathlib.Path) -> None:
    """Test file handling when all file formats are correct

    Args:
        tmp_path (pathlib.Path): path to internal pytest directory holding temporary files
    """

    # Arrange
    suffixes = [".txt", ".txt", ".txt"]
    filePaths: list[pathlib.Path] = []
    for i, suffix in enumerate(suffixes):
        filePaths.append(tmp_path.joinpath(f"file{i}{suffix}"))
        with open(filePaths[i], "w") as file:
            file.write(f"{i}")

    strFilePaths = [str(filePath) for filePath in filePaths]

    # Act
    with patch(
        "tkinter.filedialog.askopenfilenames",
        return_value=strFilePaths,
    ):
        returnPaths = fileOpen(".txt")

    # Assert
    assert len(returnPaths) == 3
    for path in returnPaths:
        assert path.suffix == ".txt"
