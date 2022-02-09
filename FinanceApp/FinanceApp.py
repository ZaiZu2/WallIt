#! python3

import xml.etree.ElementTree as ET
import copy, os, csv, datetime, sys
import tkinter as tk
from tkinter import filedialog
from typing import Tuple, Type, List
import psycopg2
from psycopg2 import sql



class TransactionService:

    pass

class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self) -> None:
        self.name: str | None = None
        self.title: str | None = None
        self.amount: float | None =  None
        self.currency: str | None = None
        self.srcAmount: float | None =  None
        self.srcCurrency: str | None = None
        self.date: datetime.datetime | None = None
        self.place: str | None  = None
        self.category: str | None = None

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


    def convertSavedRecord(self) -> None:
        """Clean up the loaded-up record - change strings to correct varTypes, replace empty strings with None"""

        def convertAmounts(string):
            """Split "[129.0, 'CZK']" string into [129.0 , 'CZK']"""
            tempAmount = []
            tempCurrency = []
            for character in string:
                try:
                    if character.isdigit() or character == '.':
                        tempAmount.append(character)
                    if character.isalpha():
                        tempCurrency.append(character)
                except ValueError:
                    pass
            return [float(''.join(tempAmount)), str(''.join(tempCurrency))]

        # check if following properties are not strings
        if type(self.date) is str:
            self.date = datetime.datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S')
        if type(self.amount) is str: # check if amount is str and needs conversion
            self.amount = float(self.amount)
        if (type(self.srcAmount) is str) and self.srcAmount: # check if 'amount is str & not empty' and needs conversion
            self.srcAmount = float(self.srcAmount)
        
        # replace values with empty strings with None
        for key, value in vars(self).items():
            if not value:
                self.__dict__[key] = None


    def categorizeRecord(self, targetCategory):
        """Assign a category to the record"""

        # ['salary', 'restaurant', 'sport', 'electronics', 'bill', 'activity', 'other']
        self.category = targetCategory


class TransactionRepo:
    """Class cointaining temporary transaction data and handling connection and queries to the DB"""

    def __init__(self):
        self.repo: list[Transaction] = []
        self.columnDict: dict = {
            'name' : 'info',
            'title' : 'title', 
            'amount' : 'amount',
            'currency' : 'currency',
            'srcAmount' : 'src_amount',
            'srcCurrency' : 'src_currency',
            'date' : 'transaction_date',
            'place' : 'place',
            'category' : 'category'}
        self.tableName = 'transactions'
        self.upsertReq = 'upsert_req'

        try:
            self.conn = psycopg2.connect("dbname=financeapp user=zaizu port=5433")
            self.cur = self.conn.cursor()
            print('Succesfully connected to the database.')
        except:
            print('Cannot connect to the database.')

    def upsertRepo(self) -> None:
        """UPSERT the DB with the currently stored changes"""

        mappedColumns= sql.SQL(', ').join(map(sql.Identifier, tuple(self.columnDict.values())))

        for transaction in self.repo:
            query = self.cur.mogrify(sql.SQL("""INSERT INTO {}({}) 
                                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                                                ON CONFLICT ON CONSTRAINT {}
                                                DO NOTHING;""").format(sql.Identifier(self.tableName), mappedColumns, sql.Identifier(self.upsertReq)),
                (transaction.name, transaction.title, transaction.amount, transaction.currency, transaction.srcAmount, transaction.srcCurrency, transaction.date, transaction.place, transaction.category))
            self.cur.execute(query)
            #print(query.decode())
        self.conn.commit()

    def appendWithoutDuplicates(self, records: list[Transaction]) -> None:
        """Append list to transaction table with no repeating records"""

        for record in records:
            duplicate = False
            for checkedRecord in self.repo:
                if record == checkedRecord:
                    duplicate = True
                    break

            if duplicate is False: 
                self.repo.append(record)

    
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
        
    
    def loadFromCSV(self) -> None:
        """Load transaction table from .CSV"""
        while True:
            try:
                with open('save.csv', 'r', newline='') as saveFile:
                    reader = csv.DictReader(saveFile)
                    recordTable = []
                    for i, row in enumerate(reader):
                        recordTable.append(Transaction())
                        recordTable[i].__dict__ = row
                        recordTable[i].convertSavedRecord()
                break
            except FileNotFoundError:
                print('Savefile not found.')
                return 1

        self.appendWithoutDuplicates(recordTable)        
        print('Data successfully loaded.')
        

    def loadStatementXML(self):
        """Parsing an XML monthly bank account statement"""

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
        
        XMLfiles = fileTypeCheck(".xml")

        for file in XMLfiles:
            tree = ET.parse(file)
            root = tree.getroot()
            namespace = {"nms": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.06"}
            expenses = []

            for count, i in enumerate(root.findall(".//nms:Ntry", namespace)):  # Parsing transaction records
                expenses.append(copy.deepcopy(Transaction()))

                expenses[count].name = parseRecord(i, ".//nms:RltdPties//nms:Nm")
                expenses[count].title = parseRecord(i, ".//nms:Ustrd")
                expenses[count].place = parseRecord(i, ".//nms:PstlAdr/nms:TwnNm")

                expenses[count].date = parseDate(i, ".//nms:BookgDt/nms:Dt")  # Parses date to datatime object

                expenses[count].amount, expenses[count].currency = parseAmount(i, "./nms:Amt")  # Parses list [Amount, Currency]                
                expenses[count].srcAmount, expenses[count].srcCurrency  = parseAmount(i, ".//nms:InstdAmt/nms:Amt")  # Parses list [Amount, Currency]

                # Parsing just 'DBIT' or 'CRDT', then changing Amount sign if needed
                dir = parseRecord(i, "./nms:CdtDbtInd") 
                if dir == "Dbit":
                    if expenses[count].amount:
                        expenses[count].amount = -expenses[count].amount
                    if expenses[count].srcAmount:
                        expenses[count].srcAmount = -expenses[count].srcAmount

            # PARSING CHECKS
            # Check for correct expenses amounts to balance
            incSum = round(sum(expense.amount for expense in expenses), 2)
            if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
                print(f"Successfully loaded {len(expenses)} records.")
            else:
                print("Records were loaded incorrectly.")

            self.appendWithoutDuplicates(expenses)
    

    def filterTable(self, currency: str = None, lowerAmount: float = None, upperAmount: float = None, lowerDate: datetime.datetime = None, upperDate: datetime.datetime = None, category: str = None) -> list[Transaction]:
        """Filter by: date, amount, category, place, dir, currency"""
 
        def filterInRange(record: Transaction, recordParameter: str, lower, upper) -> bool:
            """Select correct filtering condition based on lower/upper filtering thresholds"""
            if recordParameter == 'amount':
                if lower is None and upper is not None:
                    return record.__getattribute__('amount') <= upper
                if lower is not None and upper is None:
                    return lower <= record.__getattribute__('amount')
                if lower is not None and upper is not None:
                    return lower <= record.__getattribute__('amount') <= upper

            if recordParameter == 'date':
                if lower is None and upper is not None:
                    return record.__getattribute__('date') <= upper
                if lower is not None and upper is None:
                    return lower <= record.__getattribute__('date')
                if lower is not None and upper is not None:
                    return lower <= record.__getattribute__('date') <= upper
        
        def filterInCurrency(record: Transaction) -> bool:
            """Check and use original currency in case the transaction was converted"""

            if (record.srcCurrency is not None) and record.srcCurrency == currency:
                return record.srcCurrency == currency  # Must be True if got there
            else:
                return record.srcCurrency == currency

        filteredTable = self.repo

        if (lowerAmount is not None) or (upperAmount is not None):
            filteredTable = list(filter(lambda record: filterInRange(record, 'amount', lowerAmount, upperAmount), filteredTable))
        if currency is not None:
            filteredTable = list(filter(lambda record: filterInCurrency(record), filteredTable))
        if (lowerDate is not None) or (upperDate is not None):
            filteredTable = list(filter(lambda record: filterInRange(record, 'date', lowerDate, upperDate), filteredTable))
        if category is not None:
            filteredTable = list(filter(lambda record: record.category == category, filteredTable))
        return filteredTable


    def writeSummary(self, startDate: datetime.datetime, endDate: datetime.datetime) -> None:
        """Write summary of Incoming, Outcoming, Balance for a given period of time"""

        if startDate < endDate:
            filtered = self.filterTable(None, None, None, startDate, endDate, None, None)
        else:
            return print('Select correct period of time.')

        balance = round(sum(record.amount for record in filtered), 2)
        outgoing = round(sum(record.amount for record in filtered if record.amount >= 0), 2)
        incoming = round(sum(record.amount for record in filtered if record.amount <= 0), 2)

        return print(f"""{startDate} - {endDate}\n
                        Balance: {balance}\n
                        Incoming: {incoming}\n
                        Outgoing: {outgoing}""")


def fileTypeCheck(type: str) -> Tuple:
    """Check if extension in form of '.xml' is opened"""

    while True:
        TupleOfPaths = filedialog.askopenfilenames()
        correctFileInt = 0

        for path in TupleOfPaths:
            if os.path.basename(path).endswith(f"{type}"):
                correctFileInt += 1
        
        if correctFileInt == len(TupleOfPaths): 
            return TupleOfPaths
        else:
            print(f'{len(TupleOfPaths) - correctFileInt} files have incorrect extension. Repeat.')


def main():
    repo = TransactionRepo()

    repo.loadStatementXML()
    #table.saveToCSV()

    #table.loadFromCSV()
    repo.upsertRepo()
    

    #print('a')
    #print(len(table.table))
    #table.saveToCSV()
    #filt = table.filterTable(None, 350, 400)

    #[print(record) for record in filt]

if __name__ == "__main__":
    main()

    