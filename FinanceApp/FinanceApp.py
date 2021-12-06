#! python 3

import xml.etree.ElementTree as ET
import copy, dataclasses, os
import tkinter as tk
from tkinter import filedialog

<<<<<<< HEAD

class transaction:
    """Data class cointaining a list of expenses"""

    expenses = []
    record = {
        "Name": None,
        "Title": None,
        "Dir": None,
        "Amount": [],
        "SrcAmount": [],
        "Date": None,
        "Place": None,
    }
=======
class TransactionTable:
    """Class cointaining a list of transactions"""
>>>>>>> tmp

    def __init__(self) -> None:
        """Create a clean a list of transactions"""

<<<<<<< HEAD

def fileTypeCheck(type):
=======
        self.table = []

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

>>>>>>> tmp
    while True:
        path = filedialog.askopenfilename()

        if os.path.basename(path).endswith(f"{type}"):
            return path
        else:
            print("Wrong file type.")


def loadStatementXML():  # parsing an XML monthly bank account statement
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
<<<<<<< HEAD
    record = {
        "Name": None,
        "Title": None,
        "Dir": None,
        "Amount": [],
        "SrcAmount": [],
        "Date": None,
        "Place": None,
    }

    for count, i in enumerate(
        root.findall(".//nms:Ntry", namespace)
    ):  # Parsing expense records
        expenses.append(copy.deepcopy(record))
=======
    record = Transaction()

    for count, i in enumerate(root.findall(".//nms:Ntry", namespace)
    ):  # Parsing expense records
        expenses.append(copy.deepcopy(record.parameter))
>>>>>>> tmp

        expenses[count]["Name"] = parseRecord(i, ".//nms:RltdPties//nms:Nm")
        expenses[count]["Title"] = parseRecord(i, ".//nms:Ustrd")
        expenses[count]["Date"] = parseRecord(i, ".//nms:BookgDt/nms:Dt")
        expenses[count]["Place"] = parseRecord(i, ".//nms:PstlAdr/nms:TwnNm")

<<<<<<< HEAD
        expenses[count]["Amount"] = parseAmount(
            i, "./nms:Amt"
        )  # Parses array [Amount, Currency]
        expenses[count]["SrcAmount"] = parseAmount(
            i, ".//nms:InstdAmt/nms:Amt"
        )  # Parses array [Amount, Currency]

        expenses[count]["Dir"] = parseRecord(
            i, "./nms:CdtDbtInd"
        )  # Parsing just 'DBIT' or 'CRDT' to dictionary
=======
        expenses[count]["Amount"] = parseAmount(i, "./nms:Amt")  # Parses array [Amount, Currency]
        expenses[count]["SrcAmount"] = parseAmount(i, ".//nms:InstdAmt/nms:Amt")  # Parses array [Amount, Currency]

        expenses[count]["Dir"] = parseRecord(i, "./nms:CdtDbtInd")  # Parsing just 'DBIT' or 'CRDT' to dictionary
>>>>>>> tmp
        if expenses[count]["Dir"] == "Dbit":
            expenses[count]["Dir"] = -1
        else:
            expenses[count]["Dir"] = 1

    # PARSING CHECKS
    # Check for correct expenses amounts to balance
<<<<<<< HEAD
    incSum = round(
        sum(expense["Dir"] * expense["Amount"][0] for expense in expenses), 2
    )
=======
    incSum = round(sum(expense["Dir"] * expense["Amount"][0] for expense in expenses), 2)
>>>>>>> tmp
    if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
        print(f"Successfully loaded {len(expenses)} records.")
    else:
        print("Records were loaded incorrectly.")

    return expenses
<<<<<<< HEAD


root = tk.Tk()
root.withdraw()

filePath = tk.filedialog.askopenfilename()

loadStatementXML()

ala = transaction()
=======

def saveToCSV(records: transactionTable):
    with open('save.csv', 'w', newline='') as saveFile:
        writer = csv.DictWriter(saveFile, fieldnames = [key for key in transaction.record.keys()])
        writer.writeheader()
        writer.writerows(records)
    print('Data successfully saved.')

def loadFromCSV():
    with open('save.csv', 'r', newline='') as saveFile:
        reader = csv.DictReader(saveFile)  #fieldnames = [key for key in transaction.record.keys()]    
        savedRecords = []
        for row in reader:
            savedRecords.append(row)

    print('Data successfully loaded.')          
    return savedRecords



table = TransactionTable()

root = tk.Tk()
root.withdraw()

rec = loadStatementXML()
[table.table.append(record) for record in rec]
print(len(table.table))
>>>>>>> tmp
