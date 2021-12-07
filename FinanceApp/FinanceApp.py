#! python 3

import xml.etree.ElementTree as ET
import copy, dataclasses, os, csv
import tkinter as tk
from tkinter import filedialog

class TransactionTable:
    """Class cointaining a list of transactions"""

    def __init__(self) -> None:

        self.table = []


    def appendWithoutDuplicates(self, records: list) -> None:
        """Append list to transaction table with no repeating records"""

        for record in records:
            duplicate = False
            for checkedRecord in self.table:
                if record == checkedRecord:
                    duplicate = True
                    break

            if duplicate == False: 
                self.table.append(record)


    def saveToCSV(self) -> None:
        """Save transaction table to .CSV"""

        with open('save.csv', 'w', newline='') as saveFile:
            writer = csv.DictWriter(saveFile, fieldnames = [key for key in Transaction().parameter.keys()])
            writer.writeheader()
            writer.writerows(self.table)
        print('Data successfully saved.')


    def loadFromCSV(self) -> None:
        """Load transaction table from .CSV"""

        try:
            with open('save.csv', 'r', newline='') as saveFile:
                reader = csv.DictReader(saveFile)  #fieldnames = [key for key in transaction.record.keys()]    
                savedRecords = []
                for row in reader:
                    savedRecords.append(row)

            self.appendWithoutDuplicates(savedRecords)        
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
        record = Transaction()

        for count, i in enumerate(root.findall(".//nms:Ntry", namespace)):  # Parsing expense records
            expenses.append(copy.deepcopy(record.parameter))

            expenses[count]["Name"] = parseRecord(i, ".//nms:RltdPties//nms:Nm")
            expenses[count]["Title"] = parseRecord(i, ".//nms:Ustrd")
            expenses[count]["Date"] = parseRecord(i, ".//nms:BookgDt/nms:Dt")
            expenses[count]["Place"] = parseRecord(i, ".//nms:PstlAdr/nms:TwnNm")

            expenses[count]["Amount"] = parseAmount(i, "./nms:Amt")  # Parses array [Amount, Currency]
            expenses[count]["SrcAmount"] = parseAmount(i, ".//nms:InstdAmt/nms:Amt")  # Parses array [Amount, Currency]

            expenses[count]["Dir"] = parseRecord(i, "./nms:CdtDbtInd")  # Parsing just 'DBIT' or 'CRDT' to dictionary
            if expenses[count]["Dir"] == "Dbit":
                expenses[count]["Dir"] = -1
            else:
                expenses[count]["Dir"] = 1

        # PARSING CHECKS
        # Check for correct expenses amounts to balance
        incSum = round(sum(expense["Dir"] * expense["Amount"][0] for expense in expenses), 2)
        if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
            print(f"Successfully loaded {len(expenses)} records.")
        else:
            print("Records were loaded incorrectly.")

        self.appendWithoutDuplicates(expenses)


class Transaction:
    """Class cointaining a transaction record"""

    def __init__(self) -> None:
        """Create a clean transaction record"""

        self.parameter = {
            "Name": None,
            "Title": None,
            "Dir": None,
            "Amount": [None, None],
            "SrcAmount": [None, None],
            "Date": None,
            "Place": None,
        }

def fileTypeCheck(type: str) -> str:
    """Check if correct file type is opened"""

    while True:
        path = filedialog.askopenfilename()

        if os.path.basename(path).endswith(f"{type}"):
            return path
        else:
            print("Wrong file type.")

table = TransactionTable()

root = tk.Tk()
root.withdraw()

table.loadStatementXML()
table.saveToCSV()
print(table.table[0])
