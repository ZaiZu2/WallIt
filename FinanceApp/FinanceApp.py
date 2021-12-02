#! python 3

import xml.etree.ElementTree as ET
import copy, dataclasses, os, csv
import tkinter as tk
from tkinter import filedialog

class transactionTable:
    """Data class cointaining a transaction"""

    table = []

class transaction:
    """Data class cointaining a transaction"""

    record = {
        "Name": None,
        "Title": None,
        "Dir": None,
        "Amount": [],
        "SrcAmount": [],
        "Date": None,
        "Place": None,
        "Category": None,     
    }

    def __init__(self) -> None:
        pass

def loadStatementXML():
    """"Parsing expense data from Equabank XML monthly statement"""

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

    # OPENING XML
    while True:
        XMLpath = filedialog.askopenfilename() # TODO: Opening file in fileTypeCheck???
        if  os.path.basename(XMLpath).endswith(".xml"):
            break
    tree = ET.parse(XMLpath)
    root = tree.getroot()

    namespace = {"nms": "urn:iso:std:iso:20022:tech:xsd:camt.053.001.06"}
    
    listOfExpenses = []
    
    # PARSING ENTRIES FROM XML
    for i, entry in enumerate(root.findall(".//nms:Ntry", namespace)):
        listOfExpenses.append(copy.deepcopy(transaction.record))

        listOfExpenses[i]["Name"] = parseRecord(entry, ".//nms:RltdPties//nms:Nm")
        listOfExpenses[i]["Title"] = parseRecord(entry, ".//nms:Ustrd")
        listOfExpenses[i]["Date"] = parseRecord(entry, ".//nms:BookgDt/nms:Dt")
        listOfExpenses[i]["Place"] = parseRecord(entry, ".//nms:PstlAdr/nms:TwnNm")

        listOfExpenses[i]["Amount"] = parseAmount(entry, "./nms:Amt")  # Parses array [Amount, Currency]
        listOfExpenses[i]["SrcAmount"] = parseAmount(entry, ".//nms:InstdAmt/nms:Amt")  # Parses array [Amount, Currency]

        listOfExpenses[i]["Dir"] = parseRecord(entry, "./nms:CdtDbtInd")  # Parsing just 'DBIT' or 'CRDT' to dictionary
        if listOfExpenses[i]["Dir"] == "Dbit":
            listOfExpenses[i]["Dir"] = -1
        else:
            listOfExpenses[i]["Dir"] = 1

    # PARSING CHECKS
    # Check if expense sum equals parsed balance value
    incSum = round(sum(expense["Dir"] * expense["Amount"][0] for expense in listOfExpenses), 2)
    if incSum == round(float(root.find(".//nms:TtlNtries/nms:Sum", namespace).text), 2):
        print(f"Successfully loaded {len(listOfExpenses)} records.")
    else:
        print("Records were loaded incorrectly.")

    return listOfExpenses


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

root = tk.Tk()
root.withdraw()

dub = transactionTable()
#dub.table.extend(loadStatementXML())

#saveToCSV(dub.table)
dub.table.extend(loadFromCSV())
for rec in dub.table:
    print(rec)
