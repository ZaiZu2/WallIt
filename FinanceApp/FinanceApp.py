#! python3

import xml.etree.ElementTree as ET
import copy, os, csv, datetime, sys
import tkinter as tk
from tkinter import filedialog
import pprint
from typing import Tuple, Type, List

from dateutil.relativedelta import relativedelta
from dateutil.rrule import rrule, MONTHLY
import itertools
import psycopg2
from psycopg2.sql import SQL, Identifier, Placeholder, Composed
import configparser


class TransactionService:

    pass

class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self):
        self.id: int | None = None
        self.name: str | None = None
        self.title: str | None = None
        self.amount: float | None =  None
        self.currency: str | None = None
        self.srcAmount: float | None =  None
        self.srcCurrency: str | None = None
        self.date: datetime.datetime | None = None
        self.place: str | None  = None
        self._category: str | None = None

        self.categories: tuple = ('savings', 'grocery', 'rent', 'bills', 'restaurants', 'holidays', 'hobbies', 'experiences', 'presents', 'petty expenses')

    def queryList(self) -> list: 
        """returns transaction attributes in a modifiable, ordered list"""
        return [self.name, self.title, self.amount, self.currency, self.srcAmount, self.srcCurrency, self.date, self.place, self.category]


    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}: {self.name}, {self.amount} {self.currency}, {self.date}'


    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return TypeError
        
        return (self.name == other.name and 
                self.title == other.title and
                self.amount == other.amount and
                self.date == other.date and
                self.place == other.place) 

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
    

def fileOpen(type: str) -> Tuple[str]:
    """Opens multiple files and checks for specified extension (e.g. '.xml')\n
    returns Tuple[paths] or empty string 
    """

    while True:
        TupleOfPaths: tuple[str] = filedialog.askopenfilenames()
        correctFileInt = 0

        for path in TupleOfPaths:
            if os.path.basename(path).endswith(f"{type}"):
                correctFileInt += 1
        
        if correctFileInt == len(TupleOfPaths): 
            return TupleOfPaths
        else:
            print(f'{len(TupleOfPaths) - correctFileInt} files have incorrect extension. Repeat.')


def readDatabaseConfig(filePath: str) -> tuple[dict, dict, dict]:
    """Read DB config file and returns dict of config parameters"""

    config = configparser.RawConfigParser()
    config.optionxform = lambda option: option # preserve case-sensitivity of keys/values
    config.read(filePath)

    postgresConfig: dict = {}
    columnMap: dict = {}
    tableNames: dict = {}

    # read separate blocks and extract key-value pairs
    try:
        for key in config['postgresql']:
            postgresConfig[key] = config['postgresql'][key]

        for key in config['columnMap']:
            columnMap[key] = config['columnMap'][key]

        for key in config['tables']:
            tableNames[key] = config['tables'][key]
    except:
        print('Corrupted .ini file')

    return postgresConfig, tableNames, columnMap


class TransactionRepo:
    """Class cointaining temporary transaction data and handling connection and queries to the DB"""

    def __init__(self):
        # postgresConfig - maps DB connection info
        # tableNames - specifies used tables in DB
        # DBcolumnMap - map DB columns to Transaction class
        postgresConfig, tableNames, self.DBcolumnMap = readDatabaseConfig('db.ini')

        self.repo: list[Transaction] = []
        self.tableName: str = tableNames['tableName']
        self.upsertReq = 'upsert_req' # Internal postgresql constraint for row uniqueness

        self._decToFloat()
        try:
            self.conn = psycopg2.connect(**postgresConfig)
            self.cur = self.conn.cursor()
            print('Succesfully connected to the database.')
        except:
            print('Cannot connect to the database.')

    def _decToFloat(self):
        """Cast decimal database type to Python float type, instead of the default Decimal"""

        DEC2FLOAT = psycopg2.extensions.new_type(
        psycopg2.extensions.DECIMAL.values,
        'DEC2FLOAT',
        lambda value, curs: float(value) if value is not None else None)
        psycopg2.extensions.register_type(DEC2FLOAT)
        

    def updateRepo(self) -> None:
        """Update the DB with modified transactions with the use of common transaction ID"""
        
        for transaction in self.repo:
            query = self.cur.mogrify(SQL("""UPDATE {}
                                            SET {} = {},
                                                {} = {},
                                                {} = {},
                                                {} = {}
                                            WHERE {} = {};""").format(
                                                Identifier(self.tableName), 
                                                Identifier(self.DBcolumnMap['name']), Placeholder(name='name'),
                                                Identifier(self.DBcolumnMap['title']), Placeholder(name='title'),
                                                Identifier(self.DBcolumnMap['place']), Placeholder(name='place'),
                                                Identifier(self.DBcolumnMap['category']), Placeholder(name='category'),
                                                Identifier(self.DBcolumnMap['id']), Placeholder(name='id')),
                                            {'name': transaction.name, 'title': transaction.title, 'place': transaction.place, 
                                            'category': transaction.category, 'id': transaction.id})
            self.cur.execute(query)
            print(query.decode())
        self.conn.commit()


    def upsertRepo(self) -> None:
        """Insert temporarily stored transactions to the DB, while ignoring duplicates"""

        for transaction in self.repo:
            query = self.cur.mogrify(SQL("""INSERT INTO {}({}) s
                                                VALUES ({})
                                                ON CONFLICT ON CONSTRAINT {}
                                                DO NOTHING;""").format(
                                                    Identifier(self.tableName), 
                                                    SQL(', ').join(map(Identifier, tuple(self.DBcolumnMap.values()))), 
                                                    SQL(', ').join(Placeholder() * len(transaction.queryList())), 
                                                    Identifier(self.upsertReq)), 
                                                transaction.queryList())
            self.cur.execute(query)
            print(query.decode())
        self.conn.commit()

    def filterRepo(self, **kwarg) -> list[Transaction]:
        """Filter the DB for specific records\n
        amount = (min: float, max: float)\n
        currency = ('CZK': str, ...)\n
        srcAmount = (min: float, max: float)\n
        srcCurrency = ('CZK': str, ...)\n
        date = (min: datetime.datetime, max: datetime.datetime)\n
        category = ('grocery': str, ...)
        """

        filters = []
        filterValues = []

        # amount - 'amount BETWEEN %s AND %s'
        if 'amount' in kwarg.keys():
            amountFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.DBcolumnMap['amount']))

            filters.append(amountFilter)
            filterValues.extend(kwarg['amount'])

        # currency - 'currency IN (%s, ...)'
        if 'currency' in kwarg.keys():
            currencyFilter = SQL("{} IN ({})").format(
                Identifier(self.DBcolumnMap['currency']),
                SQL(', ').join(Placeholder() * len(kwarg['currency'])))

            filters.append(currencyFilter)
            filterValues.extend(kwarg['currency'])

        # srcAmount - 'src_amount BETWEEN %s AND %s'
        if 'srcAmount' in kwarg.keys():
            srcAmountFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.DBcolumnMap['srcAmount']))

            filters.append(srcAmountFilter)
            filterValues.extend(kwarg['srcAmount'])

        # srcCurrency - 'src_currency IN (%s, ...)'
        if 'srcCurrency' in kwarg.keys():
            srcCurrencyFilter = SQL("{} IN ({})").format(
                Identifier(self.DBcolumnMap['srcCurrency']),
                SQL(', ').join(Placeholder() * len(kwarg['srcCurrency'])))

            filters.append(srcCurrencyFilter)
            filterValues.extend(kwarg['srcCurrency'])

        # date - 'transaction_date BETWEEN %s AND %s'
        if 'date' in kwarg.keys():
            dateFilter = SQL("{} BETWEEN %s AND %s").format(
                Identifier(self.DBcolumnMap['date']))

            filters.append(dateFilter)
            filterValues.extend(kwarg['date'])

        # category - 'category IN (%s, ...)'
        if 'category' in kwarg.keys():
            categoryFilter = SQL("{} IN ({})").format(
                Identifier(self.DBcolumnMap['category']),
                SQL(', ').join(Placeholder() * len(kwarg['category'])))

            filters.append(categoryFilter)
            filterValues.extend(kwarg['category'])

        temp: list[Transaction] = []
        query = self.cur.mogrify(SQL("SELECT * FROM {} WHERE {};").format(
                                                Identifier(self.tableName),
                                                SQL(' AND ').join(
                                                    [Composed(filter) for filter in filters])),
                                            filterValues)                                   
        self.cur.execute(query)
        print(query.decode())
        
        for i, row in enumerate(self.cur.fetchall()): 
            temp.append(copy.deepcopy(Transaction()))
            temp[i].id = row[0]
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

    def monthlySummary(self) -> list[tuple]:
        """Return list of monthly incoming/outcoming/difference summaries"""

        # Extract the newest and oldest transaction in the DB
        query = self.cur.mogrify(SQL("SELECT MIN({}), MAX({}) FROM {}").format(
            Identifier(self.DBcolumnMap['date']),
            Identifier(self.DBcolumnMap['date']),
            Identifier(self.tableName)))
        #print(query.decode())
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
                                                        SUM (CASE
                                                                WHEN {} >= 0 THEN {}
                                                            ELSE 0
                                                                END) AS incoming,
                                                        SUM (CASE
                                                                WHEN {} < 0 THEN {}
                                                                ELSE 0
                                                            END) AS outgoing,
                                                        SUM ({}) AS difference
                                                    FROM {}
                                                    WHERE {}  
                                                        BETWEEN %s 
                                                        AND %s;""").format(
                                                            *[Identifier(self.DBcolumnMap['amount'])]*5,
                                                            Identifier(self.tableName),
                                                            Identifier(self.DBcolumnMap['date'])), 
                                                        (str(date),
                                                        str(date + relativedelta(months=+1))))
                #print(query.decode())
                self.cur.execute(query)
                tempSummary.append(self.cur.fetchone())

        return tempSummary
    
    def saveToCSV(self) -> None:
        """Save transaction table to .CSV"""

        # Temporary list of dictionaries is created to work as an input for 'writerows'
        tempSaveTable: list = []
        for i, record in enumerate(self.repo):
            tempSaveTable.append({})
            tempSaveTable[i] = vars(record)

        with open('save.csv', 'w', newline='') as saveFile:
            writer = csv.DictWriter(saveFile, fieldnames = [key for key in vars(self.repo[0]).keys()])
            writer.writeheader()
            writer.writerows(tempSaveTable)

        print('Data successfully saved.')
        
    def loadRevolutStatement(self) -> list[Transaction]:
        """Load Revolut monthly bank account statement"""

        # Maps Revolut CSV columns to Transaction class
        revolutColumnMap: dict = {
            'name' : 'Type', 
            'date' : 'Completed Date', 
            'title' : 'Description', 
            'amount' : 'Amount', 
            'currency' : 'Currency' 
        }

        CSVpaths = fileOpen('.csv')

        temp: list[Transaction] = []
        for path in CSVpaths:
            with open(path, 'r', newline='') as csvFile:
                reader = csv.DictReader(csvFile)
                for i, row in enumerate(reader):
                    temp.append(copy.deepcopy(Transaction()))
                    temp[i].name = row['Description']
                    temp[i].title = row['Type']
                    temp[i].amount = float(row['Amount'])
                    temp[i].currency = row['Currency']
                    temp[i].date = datetime.datetime.strptime(row['Completed Date'], '%Y-%m-%d %H:%M:%S')
        return temp


    def loadEquabankStatement(self) -> list[Transaction]:
        """Parsing Equabank monthly bank account statement"""

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
            value = []
            try:
                value.append(float(rootObj.find(XPath, namespace).text))
                value.append(rootObj.find(XPath, namespace).get("Ccy"))
            except AttributeError:
                value = [None, None]
            return value
        
        def parseDate(rootObj, XPath):
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

                temp[i].date = parseDate(rootDir, ".//nms:BookgDt/nms:Dt")  # Parses date to datatime object

                temp[i].amount, temp[i].currency = parseAmount(rootDir, "./nms:Amt")  # Parses list [Amount, Currency]                
                temp[i].srcAmount, temp[i].srcCurrency  = parseAmount(rootDir, ".//nms:InstdAmt/nms:Amt")  # Parses list [Amount, Currency]

                # Parsing just 'DBIT' or 'CRDT', then changing Amount sign if needed
                dir = parseRecord(rootDir, "./nms:CdtDbtInd") 
                if dir == "Dbit":
                    if temp[i].amount:
                        temp[i].amount = -temp[i].amount
                    if temp[i].srcAmount:
                        temp[i].srcAmount = -temp[i].srcAmount

            # PARSING CHECKS
            # Check for correct expenses amounts to balance
            incSum = round(sum([transaction.amount for transaction in temp]), 2)
            if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
                print(f"Successfully loaded {len(temp)} records.")
            else:
                print("Records were loaded incorrectly.")
 
        return temp



def main():
    repo = TransactionRepo()
    repo.repo = repo.loadRevolutStatement()


    #repo.updateRepo()
    #repo.upsertRepo()
    #repo.monthlySummary()

    #print(len(table.table))
    #table.saveToCSV()
    #filt = table.filterTable(None, 350, 400)

    #[print(record) for record in filt]


if __name__ == "__main__":
    main()

    