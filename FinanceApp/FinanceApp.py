#! python 3

import xml.etree.ElementTree as ET
import copy, dataclasses, os, csv
import tkinter as tk
from tkinter import filedialog
from typing import Type, List, Optional

# TODO: loadFromCSV loads strings of old data instead of different variables, which confuses appendWithoutDuplicates() which compares strings to different variables

class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self) -> None:

        self.parameters = {
            "Name": None,
            "Title": None,
            "Dir": None,
            "Amount": [None, None],
            "SrcAmount": [None, None],
            "Date": None,
            "Place": None,
        }

        self.category = None


    def categorizeRecord(self, category):
        """Assign a category to the record"""

        # ['salary', 'restaurant', 'sport', 'electronics', 'bill', 'activity', 'other']
        self.category = category


class TransactionTable:
    """Class cointaining a list of transactions"""

    def __init__(self) -> None:

        self.table: list[Transaction] = []


    def appendWithoutDuplicates(self, records: list[Transaction]) -> None:
        """Append list to transaction table with no repeating records"""

        for record in records:
            duplicate = False
            for checkedRecord in self.table:
                if record.parameters == checkedRecord.parameters:
                    duplicate = True
                    break

            if duplicate is False: 
                self.table.append(record)


    def saveToCSV(self) -> None:
        """Save transaction table to .CSV"""

        # I need to use tempSaveTable for saving to .csv
        # passing 'record.parameters' straight to a looped 'writerow' doesn't work
        # No clue why
        tempSaveTable: list = []
        for i, record in enumerate(self.table):
            tempSaveTable.append(copy.deepcopy({}))
            tempSaveTable[i] = record.parameters

        with open('save.csv', 'w', newline='') as saveFile:
            writer = csv.DictWriter(saveFile, fieldnames = [key for key in Transaction().parameters.keys()])
            writer.writeheader()
            writer.writerows(tempSaveTable)

        print('Data successfully saved.')


    def loadFromCSV(self) -> None:
        """Load transaction table from .CSV"""

        try:
            with open('save.csv', 'r', newline='') as saveFile:
                reader = csv.DictReader(saveFile)  #fieldnames = [key for key in transaction.record.keys()]

                recordTable = []
                for i, row in enumerate(reader):
                    recordTable.append(Transaction())
                    recordTable[i].parameters = row

            self.appendWithoutDuplicates(recordTable)        
            print('Data successfully loaded.')
        
        except FileNotFoundError:
            print('Savefile not found.')


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

        path = fileTypeCheck(".xml")
        tree = ET.parse(path)
        root = tree.getroot()
        namespace = {"nms": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.06"}
        expenses = []

        for count, i in enumerate(root.findall(".//nms:Ntry", namespace)):  # Parsing transaction records
            expenses.append(copy.deepcopy(Transaction()))

            expenses[count].parameters["Name"] = parseRecord(i, ".//nms:RltdPties//nms:Nm")
            expenses[count].parameters["Title"] = parseRecord(i, ".//nms:Ustrd")
            expenses[count].parameters["Date"] = parseRecord(i, ".//nms:BookgDt/nms:Dt")
            expenses[count].parameters["Place"] = parseRecord(i, ".//nms:PstlAdr/nms:TwnNm")

            expenses[count].parameters["Amount"] = parseAmount(i, "./nms:Amt")  # Parses list [Amount, Currency]
            expenses[count].parameters["SrcAmount"] = parseAmount(i, ".//nms:InstdAmt/nms:Amt")  # Parses list [Amount, Currency]

            expenses[count].parameters["Dir"] = parseRecord(i, "./nms:CdtDbtInd")  # Parsing just 'DBIT' or 'CRDT' to a dictionary
            if expenses[count].parameters["Dir"] == "Dbit":
                expenses[count].parameters["Dir"] = -1
            else:
                expenses[count].parameters["Dir"] = 1

        # PARSING CHECKS
        # Check for correct expenses amounts to balance
        incSum = round(sum(expense.parameters["Dir"] * expense.parameters["Amount"][0] for expense in expenses), 2)
        if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
            print(f"Successfully loaded {len(expenses)} records.")
        else:
            print("Records were loaded incorrectly.")

        self.appendWithoutDuplicates(expenses)


def fileTypeCheck(type: str) -> str:
    """Check if extension in form of '.xml' is opened"""

    while True:
        path = filedialog.askopenfilename()

        if os.path.basename(path).endswith(f"{type}"):
            return path
        else:
            print("Wrong file type.")


def main():
    table = TransactionTable()

    print(len(table.table))
    table.loadFromCSV()
    print(len(table.table))
    table.loadStatementXML()
    print(len(table.table))
    root = tk.Tk()
    root.withdraw()

    
    #table.loadStatementXML()
    #[print(table.n.parameters) for table.n in table.table]

    table.saveToCSV()


main()