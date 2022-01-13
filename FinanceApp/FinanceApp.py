#! python 3

from tkinter.constants import S
import xml.etree.ElementTree as ET
import copy, os, csv, datetime, sys
import tkinter as tk
from tkinter import filedialog
from typing import Type, List, Optional
class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self) -> None:
        self.name: str | None = None
        self.title: str | None = None
        self.dir: int | None =  None
        self.amount: list = [None, None]
        self.srcAmount: list = [None, None]
        self.date: Optional[datetime.datetime] = None
        self.place: Optional[str]  = None
        self.category: Optional[str] = None


    def __repr__(self) -> str:
        return f'{self.__class__.__qualname__}: {self.name}, {self.dir*self.amount[0]} {self.amount[1]}, {self.date}'


    def __eq__(self, other):
        if not isinstance(other, Transaction):
            return TypeError
        
        return (self.name == other.name and 
                self.title == other.title and
                self.dir == other.dir and 
                self.amount[0] == other.amount[0] and
                self.amount[1] == other.amount[1] and
                self.date == other.date and
                self.place == other.place) 


    def convertSavedRecord(self) -> None:
        """Clean up the loaded-up record - change strings to correct varTypes, replace empty strings with None"""

        def convertDate(date):
            tempDate = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S')
            return tempDate

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
            self.date = convertDate(self.date)
        if type(self.amount) is str: # check if amount is str and needs conversion
            self.amount = convertAmounts(self.amount)
        if (type(self.srcAmount) is str) and self.srcAmount: # check if 'amount is str & not empty' and needs conversion
            self.srcAmount = convertAmounts(self.srcAmount)
        if type(self.dir) is str:
            self.dir = int(self.dir)
        
        # replace values with empty strings with None
        for key, value in vars(self).items():
            if not value:
                self.__dict__[key] = None


    def categorizeRecord(self, targetCategory):
        """Assign a category to the record"""

        # ['salary', 'restaurant', 'sport', 'electronics', 'bill', 'activity', 'other']
        self.category = targetCategory


class TransactionTable:
    """Class cointaining a list of transactions"""

    def __init__(self):
        self.table: list[Transaction] = []


    def appendWithoutDuplicates(self, records: list[Transaction]) -> None:
        """Append list to transaction table with no repeating records"""

        for record in records:
            duplicate = False
            for checkedRecord in self.table:
                if record == checkedRecord:
                    duplicate = True
                    break

            if duplicate is False: 
                self.table.append(record)

    
    def saveToCSV(self) -> None:
        """Save transaction table to .CSV"""

        # Temporary list of dictionaries is created to work as an input for 'writerows'
        tempSaveTable: list = []
        for i, record in enumerate(self.table):
            tempSaveTable.append({})
            tempSaveTable[i] = vars(record)

        with open('save.csv', 'w', newline='') as saveFile:
            writer = csv.DictWriter(saveFile, fieldnames = [key for key in vars(self.table[0]).keys()])
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
                sys.exit()

        self.appendWithoutDuplicates(recordTable)        
        print('Data successfully loaded.')
        

    def loadStatementXML(self):  # parsing an XML monthly bank account statement
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
                value = None
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

                expenses[count].amount = parseAmount(i, "./nms:Amt")  # Parses list [Amount, Currency]
                expenses[count].srcAmount = parseAmount(i, ".//nms:InstdAmt/nms:Amt")  # Parses list [Amount, Currency]

                expenses[count].dir = parseRecord(i, "./nms:CdtDbtInd")  # Parsing just 'DBIT' or 'CRDT' to a dictionary
                if expenses[count].dir == "Dbit":
                    expenses[count].dir = -1
                else:
                    expenses[count].dir = 1

            # PARSING CHECKS
            # Check for correct expenses amounts to balance
            incSum = round(sum(expense.dir * expense.amount[0] for expense in expenses), 2)
            if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
                print(f"Successfully loaded {len(expenses)} records.")
            else:
                print("Records were loaded incorrectly.")

            self.appendWithoutDuplicates(expenses)


    def writeSummary(self, start: datetime.datetime, end: datetime.datetime) -> str:
        """Write juxtaposition of Incoming, Outcoming, Balance for a given period of time"""

        # TODO: implement filtering method here
        filtered = self.table

        balance = round(sum((record.dir * record.amount[0] for record in filtered)), 2)
        outgoing = round(sum((record.dir * record.amount[0] for record in filtered if record.dir == -1)), 2)
        incoming = round(sum((record.dir * record.amount[0] for record in filtered if record.dir == 1)), 2)

        return print(f"""{datetime.datetime} - {datetime.datetime}\n
                        Balance: {balance}\n
                        Incoming: {incoming}\n
                        Outgoing: {outgoing}""")
    

    def filterTable(self, currency: str = None, lowerAmount: float = None, upperAmount: float = None, 
                    lowerDate: datetime.datetime = None, upperDate: datetime.datetime = None, 
                    dir: int = None, category: str = None) -> list(Transaction):
        """Filter by: date, amount, category, place, dir, currency"""
 
        def filterInRange(record: Transaction, recordParameter: str, lower, upper) -> bool:
            """Select correct filtering condition based on lower/upper filtering thresholds"""
            if recordParameter == 'amount':
                if lower is None and upper is not None:
                    return record.__getattribute__('amount')[0] <= upper
                if lower is not None and upper is None:
                    return lower <= record.__getattribute__('amount')[0]
                if lower is not None and upper is not None:
                    return lower <= record.__getattribute__('amount')[0] <= upper

            if recordParameter == 'date':
                if lower is None and upper is not None:
                    return record.__getattribute__('date') <= upper
                if lower is not None and upper is None:
                    return lower <= record.__getattribute__('date')
                if lower is not None and upper is not None:
                    return lower <= record.__getattribute__('date') <= upper
        
        def filterInCurrency(record: Transaction) -> bool:
            """Check and use original currency in case the transaction was converted"""

            if (record.srcAmount is not None) and record.srcAmount[1] == currency:
                return record.srcAmount[1] == currency  # Must be True if got there
            else:
                return record.amount[1] == currency

        filteredTable = self.table

        if (lowerAmount is not None) or (upperAmount is not None):
            filteredTable = list(filter(lambda record: filterInRange(record, 'amount', lowerAmount, upperAmount), filteredTable))
        if currency is not None:
            filteredTable = list(filter(lambda record: filterInCurrency(record), filteredTable))
        if dir is not None:
            filteredTable = list(filter(lambda record: record.dir == dir, filteredTable))
        if (lowerDate is not None) or (upperDate is not None):
            filteredTable = list(filter(lambda record: filterInRange(record, 'date', lowerDate, upperDate), filteredTable))
        if category is not None:
            filteredTable = list(filter(lambda record: record.category == category, filteredTable))
        return filteredTable


def fileTypeCheck(type: str) -> str:
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
    table = TransactionTable()

    #print(len(table.table))
    table.loadFromCSV()
    print(len(table.table))
    #table.loadStatementXML()
    #print(len(table.table))
    print(repr(table.table[10]))
    table.saveToCSV()
    table.writeSummary(0,0)
    #print(len(table.table))
    #table.loadStatementXML()
    #print(len(table.table))
    #print(repr(table.table[10]))
    #table.saveToCSV()
    filt = table.filterTable()
    [print(a) for a in filt]


    root = tk.Tk()
    root.withdraw() 

    
    #table.loadStatementXML()
    #[print(table.n.parameters) for table.n in table.table]

    #table.saveToCSV()


main()