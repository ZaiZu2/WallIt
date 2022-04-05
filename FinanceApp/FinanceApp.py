#! python3

from __future__ import annotations
from distutils.command.config import config
from xml.dom import InvalidAccessErr
import xml.etree.ElementTree as ET
import copy
import csv
import datetime
from tkinter import filedialog
import pprint
import functools

from typing import Generator
from contextlib import contextmanager
import pathlib
from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
import psycopg2, psycopg2.extensions
from psycopg2.sql import SQL, Identifier, Placeholder, Composed
import configparser
from typing import TypeVar

T = TypeVar("T")

def _dec2float(value: str | None, cur: object) -> float | None:
    return None if value is None else float(value)

@functools.lru_cache(maxsize=0)
def _dec2floatType() -> object:
    return psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values, "DEC2FLOAT", _dec2float
    )

class CaseSensitiveConfigParser(configparser.ConfigParser):
    def optionxform(self, value: T) -> T:
        """Preserve case-sensitivity of keys/values while reading config file"""
        return value

class InvalidConfigError(Exception):
    pass

class Session:
    """Main class holding user session"""

    def __init__(self, user):
        self.user: User = user
        self.service: TransactionService = TransactionService()

        self.tempTransactions: list[Transaction] | None = None

class User:
    """Class representing logged-in user"""

    def __init__(self):
        self.userId: int | None = None
        self.username: str | None = None
        self.password: str = None
        self.firstName: str | None = None
        self.lastName: str | None = None

    def __repr__(self) -> str:
        return f'{self.firstName} {self.lastName} under username {self.username}'

class TransactionService:
    pass

class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self):
        self.transactionId: int | None = None
        self.name: str | None = None
        self.title: str | None = None
        self.amount: float | None =  None
        self.currency: str | None = None
        self.srcAmount: float | None =  None
        self.srcCurrency: str | None = None
        self.date: datetime.datetime | None = None
        self.place: str | None  = None
        self._category: str | None = None
        self.userId: int | None = None
        self.bankId: int | None = None
        self.bankName: str | None = None

        self.categories: tuple = ('savings', 'grocery', 'rent', 'bills', 'restaurants', 'holidays', 'hobbies', 'experiences', 'presents', 'petty expenses', None)

    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}: {self.name}, {self.amount} {self.currency}, {self.date}'

    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return TypeError
        
        return (self.name, self.title, self.amount, self.date, self.place) == (other.name, other.title, other.amount, other.date, other.place)

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        """Additionally check if category exists in the list of categories"""
        
        if value in self.categories:
            self._category = value
        else:
            print('There is no such category. Category not updated.')

    def queryList(self) -> list: 
        """Returns transaction attributes in a modifiable, ordered list

        Returns:
            list: ordered list of Transaction attributes
        """
        return [self.name, self.title, self.amount, self.currency, self.srcAmount, self.srcCurrency, self.date, self.place, self.category, self.userId, self.bankId, self.bankName]

class TransactionRepo:
    """Class cointaining temporary transaction data and handling connection and queries to the DB during session"""

    @classmethod
    @contextmanager
    def establishConnection(cls) -> Generator[TransactionRepo, None, None]:
        """Load database config parameters.
        Create ContextManager handling connection with the database.

        Raises:
            InvalidConfigError: raised due to unexpected postgresConfig.ini formatting

        Yields:
            Generator[TransactionRepo, None, None]: generate repo instance
        """
        
        # Read config file
        config = CaseSensitiveConfigParser()
        configFilePath = pathlib.Path(__file__).parents[1].joinpath('config','postgresConfig.ini')
        config.read(configFilePath)

        try:
            # Read separate config sections and extract key-value pairs
            postgresConfig = {}
            section = config['postgresql']
            postgresConfig['host'] = section['host']
            postgresConfig['database'] = section['database']
            postgresConfig['user'] = section['user']
            postgresConfig['password'] = section['password']
            postgresConfig['port'] = section['port']
        except KeyError as e:
            raise InvalidConfigError('Unexpected postgresConfig.ini formatting') from e

        a = psycopg2.connect(**postgresConfig) # Temporary variable to not handle connect() with try block
        try:
            with a as connection:
                # Ensure that DECIMAL postgres data type is cast by default to Float and not Decimal
                psycopg2.extensions.register_type(_dec2floatType(), connection)
                with connection.cursor() as cursor:
                    yield cls(connection, cursor)
        finally:
            connection.close()

    def __init__(self, connection: psycopg2.connection, cursor: psycopg2.cursor):
        self.conn: psycopg2.connection = connection
        self.cur: psycopg2.cursor  = cursor

        self.tableMaps: dict[str, tuple[str, dict[str, str]]] = self._loadTableMaps()
        self._bankMap: dict[str, int] = self._parseBankID()
        self.upsertReq = 'upsert_constraint' # Internal postgresql constraint for Transaction record uniqueness
 
    def _loadTableMaps(self) -> dict[str, tuple[str, dict[str, str]]]:
        """Create data structure containing dicts mapping tableNames/columnNames to Transaction attributes.

        tableMaps['name (in code)'] = ('tableName (from .ini)', {columnName (in code) : column_name (from .ini)})
        e.g.
        tableMaps['transactions'] = ('transactions', {'name':'info', 'srcAmount':'src_amount', ...})
        tableMaps['users'] = ('users', {'firstName':'first_name', 'lastName':'last_name', ...})

        Raises:
            Exception: raised in case of unexpected config file formatting

        Returns:
            dict[str, tuple[str, dict]]: 
        """
        # TODO: Current data structure (and it's creation process) is very clunky, 
        #       needs to be redone somewhat smarter
        # TODO: Current config parsing is section order sensitive. That's stupid!
    
        def checkPostgresMaps(value: str) -> None:
            """Ensure that given string is written in snake_case

            Args:
                value (str): evaluated string

            Raises:
                InvalidConfigError: due to wrong string formatting
            """

            # check if string starts or ends with '_'
            if value.startswith('_') or value.endswith('_'):
                raise InvalidConfigError('Wrong DB column map - trailing or proceeding underscore not allowed')
            # check if there are only letters and '_'
            if not value.replace('_', '').isalpha():
                raise InvalidConfigError('Wrong DB column map - non-alpha signs present')
            # check if all letter are lowercase
            if value.isupper():
                raise InvalidConfigError('Wrong DB column map - uppercase letters present')
            # check if there is a double underscore '__' in string
            for sign in value:
                repeated = 0
                if sign == '_': 
                    repeated += 1
                    if repeated == 2:
                        raise InvalidConfigError('Wrong DB column map - double underscore present')
                else: 
                    repeated = 0

        config = CaseSensitiveConfigParser()
        configFilePath = pathlib.Path(__file__).parents[1].joinpath('config','tableMaps.ini')
        config.read(configFilePath)

        mappedDicts: list[dict] = []
        # transactionsTableMap - map transactions table columns to Transaction class
        transactionsTableMap = {}
        # usersTableMap - map users table columns to Transaction class
        usersTableMap = {}
        # banksTableMap - map banks table columns to Transaction class
        banksTableMap = {}
        # callNames - in-app reference names used for calling specific tables
        callNames = ['transactions', 'users', 'banks']
        # Read separate config blocks and extract key-value pairs
        try:
            for key in config['transactions']:
                checkPostgresMaps(config['transactions'][key])
                transactionsTableMap[key] = config['transactions'][key]
            mappedDicts.append(transactionsTableMap)
            for key in config['users']:
                checkPostgresMaps(config['users'][key])
                usersTableMap[key] = config['users'][key]
            mappedDicts.append(usersTableMap)

            for key in config['banks']:
                checkPostgresMaps(config['banks'][key])
                banksTableMap[key] = config['banks'][key]
            mappedDicts.append(banksTableMap)
        except KeyError:
            raise InvalidConfigError('Unexpected tableMaps.ini formatting') 

        tableMaps: dict[str, tuple[str, dict]] = {} # data structure explained in docstring
        for callName, postgresName, mappedDict in zip(callNames, config.sections(), mappedDicts):
            tableMaps[callName] = (postgresName, mappedDict)

        return tableMaps

    def _parseBankID(self) -> dict[str, int]:
        """Query mapping of all existing bank names to their Id from DB

        Returns:
            dict[str, int]: dictionary of ['bankName': 'bankId']
        """

        query = self.cur.mogrify(SQL("""SELECT {} FROM {};""").format(
                SQL(',').join(
                    Identifier(n) for n in [
                        self.tableMaps['banks'][1]['bankId'],
                        self.tableMaps['banks'][1]['bankName']
                    ]
                ),
                Identifier(self.tableMaps['banks'][0])
            ),
        )
        print(query.decode())
        self.cur.execute(query)

        bankMap = dict((row[1], row[0]) for row in self.cur.fetchall())
        return bankMap

    def userQuery(self, username: str) -> User | None:
        """Query the DB with username to check if corresponding user exists

        Args:
            username (str): username

        Returns:
            User | None: User class if user exists, None if not
        """

        query = self.cur.mogrify(SQL("""SELECT * FROM {} WHERE {} = %s;""").format(
                Identifier(self.tableMaps['users'][0]),
                Identifier(self.tableMaps['users'][1]['username'])),
            (username,))
        self.cur.execute(query)
        print(query.decode())
        result = self.cur.fetchone()

        if result:
            temp = User()
            temp.userId = result[0]
            temp.username = result[1]
            temp.password = result[2]
            temp.firstName = result[3]
            temp.lastName = result[4]
            return temp
        else:
            print('Your username is invalid.')
            return None

    def updateRepo(self, transactions: list[Transaction]) -> None:
        """Update the DB with modified transactions with the use of common transaction ID

        Args:
            transactions (list[Transaction]): list of Transactions to be updated
        """
        
        for transaction in transactions:
            query = self.cur.mogrify(SQL("""UPDATE {}
                                            SET {} = {},
                                                {} = {},
                                                {} = {},
                                                {} = {}
                                            WHERE {} = {};""").format(
                                                Identifier(self.tableMaps['transactions'][0]), 
                                                Identifier(self.tableMaps['transactions'][1]['name']), Placeholder(name='name'),
                                                Identifier(self.tableMaps['transactions'][1]['title']), Placeholder(name='title'),
                                                Identifier(self.tableMaps['transactions'][1]['place']), Placeholder(name='place'),
                                                Identifier(self.tableMaps['transactions'][1]['category']), Placeholder(name='category'),
                                                Identifier(self.tableMaps['transactions'][1]['id']), Placeholder(name='id')),
                                            {'name': transaction.name, 'title': transaction.title, 'place': transaction.place, 
                                            'category': transaction.category, 'id': transaction.transactionId})
            print(query.decode())
            self.cur.execute(query)
        self.conn.commit()

    def upsertRepo(self, transactions: list[Transaction]) -> None:
        """Insert temporarily stored transactions to the DB, while ignoring duplicates

        Args:
            transactions (list[Transaction]): List of transactions to be upserted
        """

        tempMap = copy.copy(self.tableMaps['transactions'][1])
        tempMap.pop('transactionId')

        for transaction in transactions:
            query = self.cur.mogrify(SQL("""INSERT INTO {}({})
                                                VALUES ({})
                                                ON CONFLICT ON CONSTRAINT {}
                                                DO NOTHING;""").format(
                                                    Identifier(self.tableMaps['transactions'][0]), 
                                                    SQL(', ').join(map(Identifier, tuple(tempMap.values()))), 
                                                    SQL(', ').join(Placeholder() * len(transaction.queryList())), 
                                                    Identifier(self.upsertReq)), 
                                                transaction.queryList())
            print(query.decode())
            self.cur.execute(query)
        self.conn.commit()

    def filterRepo(self, user: User, **kwarg) -> list[Transaction]:
        """Query and filter the DB for specific records

        Args:
            user (User): user for whom the query is constructed

            filtering parameters:
            amount=(min: float, max: float)
            currency=('CZK': str, ...)
            srcAmount=(min: float, max: float)
            srcCurrency=('CZK': str, ...)
            date = (min: datetime.datetime, max: datetime.datetime)
            category=('grocery': str, ...)
            bank=('Revolut': str, ...)

        Returns:
            list[Transaction]: filtered list of transactions
        """

        filters = []
        filterValues = []

        # userId - 'userId = %s'
        userFilter = SQL("{} = %s").format(
            Identifier(self.tableMaps['transactions'][1]['userId']))

        filters.append(userFilter)
        filterValues.append(user.userId)

        # amount - 'amount BETWEEN %s AND %s'
        if 'amount' in kwarg.keys():
            amountFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.tableMaps['transactions'][1]['amount']))

            filters.append(amountFilter)
            filterValues.extend(kwarg['amount'])

        # currency - 'currency IN (%s, ...)'
        if 'currency' in kwarg.keys():
            currencyFilter = SQL("{} IN ({})").format(
                Identifier(self.tableMaps['transactions'][1]['currency']),
                SQL(', ').join(Placeholder() * len(kwarg['currency'])))

            filters.append(currencyFilter)
            filterValues.extend(kwarg['currency'])

        # srcAmount - 'src_amount BETWEEN %s AND %s'
        if 'srcAmount' in kwarg.keys():
            srcAmountFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.tableMaps['transactions'][1]['srcAmount']))

            filters.append(srcAmountFilter)
            filterValues.extend(kwarg['srcAmount'])

        # srcCurrency - 'src_currency IN (%s, ...)'
        if 'srcCurrency' in kwarg.keys():
            srcCurrencyFilter = SQL("{} IN ({})").format(
                Identifier(self.tableMaps['transactions'][1]['srcCurrency']),
                SQL(', ').join(Placeholder() * len(kwarg['srcCurrency'])))

            filters.append(srcCurrencyFilter)
            filterValues.extend(kwarg['srcCurrency'])

        # date - 'transaction_date BETWEEN %s AND %s'
        if 'date' in kwarg.keys():
            dateFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.tableMaps['transactions'][1]['date']))

            filters.append(dateFilter)
            filterValues.extend(kwarg['date'])

        # category - 'category IN (%s, ...)'
        if 'category' in kwarg.keys():
            categoryFilter = SQL("{} IN ({})").format(
                Identifier(self.tableMaps['transactions'][1]['category']),
                SQL(', ').join(Placeholder() * len(kwarg['category'])))

            filters.append(categoryFilter)
            filterValues.extend(kwarg['category'])

        # bank - 'bank_id IN (%s, ...)'
        if 'bank' in kwarg.keys():
            # map bankIds to bankNames and use them as a filtering value to keep the query simple (without a join)
            bankIdList: list = []
            for bankName in kwarg['bank']:
                bankIdList.append(self._bankMap[bankName])

            # build query using bankIds instead of bankNames
            bankFilter = SQL("{} IN ({})").format(
                Identifier(self.tableMaps['transactions'][1]['bankId']),
                SQL(', ').join(Placeholder() * len(kwarg['bank'])))

            filters.append(bankFilter)
            # use mapped bankIds as the filtering values
            filterValues.extend(bankIdList)

        temp: list[Transaction] = []
        query = self.cur.mogrify(SQL("SELECT * FROM {} WHERE {};").format(
                                                Identifier(self.tableMaps['transactions'][0]),
                                                SQL(' AND ').join(
                                                    [Composed(filter) for filter in filters])),
                                            filterValues)       
        print(query.decode())                            
        self.cur.execute(query)
        
        for i, row in enumerate(self.cur.fetchall()): 
            temp.append(copy.deepcopy(Transaction()))
            temp[i].transactionId = row[0]
            temp[i].name = row[1]
            temp[i].title = row[2]
            temp[i].amount =  row[3]
            temp[i].currency = row[4]
            temp[i].srcAmount = row[5]
            temp[i].srcCurrency = row[6]
            temp[i].date = row[7]
            temp[i].place = row[8]
            temp[i].category = row[9]

        return temp

    def monthlySummary(self, user: User) -> list[tuple]:
        """Query the DB for monthly, juxtaposed incoming/outcoming/difference values

        Args:
            user (User): user for whom the query is constructed

        Returns:
            list[tuple]: list of tuples containing incoming/outcoming/difference numbers
        """

        # Extract the newest and oldest transaction in the DB
        query = self.cur.mogrify(SQL("SELECT MIN({}), MAX({}) FROM {} WHERE {} = %s;").format(
                Identifier(self.tableMaps['transactions'][1]['date']),
                Identifier(self.tableMaps['transactions'][1]['date']),
                Identifier(self.tableMaps['transactions'][0]),
                Identifier(self.tableMaps['transactions'][1]['userId'])),
            (user.userId,))
        print(query.decode())
        self.cur.execute(query)
        startDate, endDate = self.cur.fetchone()

        # Set the boundary dates to the first day of month
        startDate = startDate - relativedelta(day=1, hour=0, minute=0, second=0)
        endDate = endDate - relativedelta(day=1, hour=0, minute=0, second=0)

        # Iterate over monthly periods, querying the database
        tempSummary: list[tuple] = []
        for date in rrule(freq=MONTHLY, dtstart=startDate, until=endDate):
            if date != endDate:  # omit last iteration
                query = self.cur.mogrify(SQL("""SELECT
                                                    COALESCE(
                                                        SUM(
                                                            CASE
                                                                WHEN {} >= 0 THEN {}
                                                                ELSE 0
                                                            END), 
                                                        0)  AS incoming,
                                                    COALESCE(                                                        
                                                        SUM(
                                                            CASE
                                                                WHEN {} < 0 THEN {}
                                                                ELSE 0
                                                            END),
                                                        0) AS outgoing,
                                                    COALESCE(SUM({}), 0) AS difference
                                                FROM {}
                                                WHERE {}  
                                                    BETWEEN %s AND %s
                                                AND
                                                    {} = %s;""").format(
                                                        *[Identifier(self.tableMaps['transactions'][1]['amount'])]*5,
                                                        Identifier(self.tableMaps['transactions'][0]),
                                                        Identifier(self.tableMaps['transactions'][1]['date']),
                                                        Identifier(self.tableMaps['transactions'][1]['userId'])), 
                                                    (str(date),
                                                    str(date + relativedelta(months=+1)),
                                                    user.userId))
                print(query.decode())
                self.cur.execute(query)

                tempSummary.append(date) # attach starting date to each summary
                tempSummary.extend(self.cur.fetchone())

        return tempSummary
        
    def loadRevolutStatement(self, user: User) -> list[Transaction]:
        """Load Transactions from Revolut monthly bank statement in .csv file format

        Args:
            user (User): user for whom the query is constructed

        Returns:
            list[Transaction]: list of Transactions which were loaded
        """

        # Maps Revolut CSV columns to Transaction class
        revolutColumnMap: dict = {
            'name' : 'Type', 
            'date' : 'Completed Date', 
            'title' : 'Description', 
            'amount' : 'Amount', 
            'currency' : 'Currency' }

        CSVpaths = fileOpen('.csv')

        temp: list[Transaction] = []
        for path in CSVpaths:
            with open(path, 'r', newline='') as csvFile:
                reader = csv.DictReader(csvFile)
                for i, row in enumerate(reader):
                    temp.append(copy.deepcopy(Transaction()))
                    temp[i].name = row['Description']
                    temp[i].title = row['Type']
                    temp[i].srcAmount = float(row['Amount'])
                    temp[i].srcCurrency = row['Currency']
                    temp[i].date = datetime.datetime.strptime(row['Completed Date'], '%Y-%m-%d %H:%M:%S')
                    temp[i].bankId = self._bankMap['Revolut']
                    temp[i].userId = user.userId
        return temp

    def loadEquabankStatement(self, user: User) -> list[Transaction]:
        """Load Transactions from Equabank monthly bank statement in .xml file format

        Args:
            user (User): user for whom the query is constructed

        Returns:
            list[Transaction]: list of Transactions which were loaded
        """

        # TODO: Handling multiple transactions which are not unique by DB standards (UNIQUE amount, currency, date)
        #       Due to incomplete/generalized transaction date in Equabank XML, it's not possible to clearly define transaction uniqueness
        #       Solution1: providing additional column in DB which indexes transactions having same (amount, currency, date) combo?
        #       Solution2: requirement from the user to manually modify date or other UNIQUEness parameter during XML loading process

        def parseRecord(rootObj, XPath):
            try:
                value = rootObj.find(XPath, namespace).text.capitalize()
            except AttributeError:
                value = None
            return value

        def parseAmount(rootObj, XPath):
            """Parse list [Amount, Currency] from Equabank XML"""
            value = []
            try:
                value.append(float(rootObj.find(XPath, namespace).text))
                value.append(rootObj.find(XPath, namespace).get("Ccy"))
            except AttributeError:
                value = [None, None]
            return value
        
        def parseDate(rootObj, XPath):
            """Parse date to datatime object from Equabank XML"""
            try:
                date = datetime.datetime.strptime(rootObj.find(XPath, namespace).text, '%Y-%m-%d+%H:%M')
            except AttributeError:
                date = None
            return date        
        
        XMLfiles = fileOpen(".xml")

        temp: list[Transaction] = []
        for file in XMLfiles:
            tree = ET.parse(file)
            root = tree.getroot()
            namespace = {"nms": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.06"}

            for i, rootDir in enumerate(root.findall(".//nms:Ntry", namespace)):  # Parsing transaction records
                temp.append(copy.deepcopy(Transaction()))

                temp[i].name = parseRecord(rootDir, ".//nms:RltdPties//nms:Nm")
                temp[i].title = parseRecord(rootDir, ".//nms:Ustrd")
                temp[i].place = parseRecord(rootDir, ".//nms:PstlAdr/nms:TwnNm")

                temp[i].date = parseDate(rootDir, ".//nms:BookgDt/nms:Dt")

                temp[i].amount, temp[i].currency = parseAmount(rootDir, "./nms:Amt")                
                temp[i].srcAmount, temp[i].srcCurrency  = parseAmount(rootDir, ".//nms:InstdAmt/nms:Amt")

                # Parsing just 'DBIT' or 'CRDT', then changing Amount sign if needed
                dir = parseRecord(rootDir, "./nms:CdtDbtInd") 
                if dir == "Dbit":
                    if temp[i].amount:
                        temp[i].amount = -temp[i].amount
                    if temp[i].srcAmount:
                        temp[i].srcAmount = -temp[i].srcAmount

                temp[i].bankId = self._bankMap['Equabank']
                temp[i].userId = user.userId
                
            # PARSING CHECKS
            # Check for correct expenses amounts to balance
            incSum = round(sum([transaction.amount for transaction in temp]), 2)
            if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
                print(f"Successfully loaded {len(temp)} records.")
            else:
                print("Records were loaded incorrectly.")
 
        return temp
    

def fileOpen(type: str) -> tuple[str]:
    """Open multiple files and checks their type. If not all files are as specified, require to select them again. 

    Args:
        type (str): expected type of files stated in '.xml' format

    Returns:
        tuple[str]: _description_
    """

    while True:
        tupleOfPaths: tuple[str, ] = filedialog.askopenfilenames()
        correctFileInt = 0

        for path in tupleOfPaths:
            if str(pathlib.Path(path)).endswith(type):
                correctFileInt += 1
        
        if correctFileInt == len(tupleOfPaths): 
            return tupleOfPaths
        else:
            print(f'{len(tupleOfPaths) - correctFileInt} files have incorrect extension. Repeat.')

def login(username: str, password: str, sessions: dict[str, Session]) -> bool:
    """Handle user log-in procedure

    Args:
        username (str): username to be verified in the log-in procedure
        password (str): password to be verified in the log-in procedure
        sessions (dict[str, Session]): dictionary of logged-in user sessions {'username': Session}

    Returns:
        bool: Return True if log-in process was successful
    """

    global repo

    # Create a session object if there's no session opened for 'username'
    if username not in sessions.keys():
        tempUser: User | None = repo.userQuery(username)
    else:
        print('User already logged in.')
        return False

    # Delete session object in case username/password check (repo.userQuery()) returned None and was unsuccessful
    if tempUser and password == tempUser.password:
        sessions[username] = Session(tempUser)
        print('User logged in.')
        return True
    else:
        print('Password invalid.')
        del sessions[username]
        return False

if __name__ == "__main__":

    with TransactionRepo.establishConnection() as repo:

        #repo = TransactionRepo()
        sessions: dict[str, Session] = {}

        loggedIn = login('ZaiZu', 'poop', sessions)
        zaizu = sessions['ZaiZu']
        #zaizu.tempTransactions = repo.loadRevolutStatement(zaizu.user)
        #repo.upsertRepo(zaizu.tempTransactions)

        do = repo.monthlySummary(zaizu.user)
        [print(repr(dod)) for dod in do]

        #po = repo.filterRepo(zaizu.user, bank=('Revolut',))
        #[print(repr(pop)) for pop in po]

        print('a')
        #repo.updateRepo()
        #repo.upsertRepo()
        #repo.monthlySummary()

        #print(len(table.table))
        #table.saveToCSV()
        #filt = table.filterTable(None, 350, 400)

        #[print(record) for record in filt]