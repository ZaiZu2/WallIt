#! python 3

from os import name
import xml.etree.ElementTree as ET


class transaction:

    def __init__(self) -> None:
        pass






def loadStatementXML(): #parsing an XML monthly bank account statement
    def parseRecord(rootObj, XPath):
        try:
            value = rootObj.find(XPath, namespace).text
        except AttributeError:
            value = None
        return value

    tree = ET.parse('statement.xml')
    root = tree.getroot()
    namespace = {'nms':'urn:iso:std:iso:20022:tech:xsd:camt.053.001.06'}

    expense = []
    record = {'Name': None, 'Dir':None, 'SrcCurr': None, 'TrgtCurr': None, 'Title': None, 'Date': None, 'Place': None}

    for count, i in enumerate(root.findall('.//nms:Ntry', namespace)):
        expense.append(record)

        # Parsing names
        expense[count]['Name'] = parseRecord(i, './/nms:RltdPties//nms:Nm')
        # Parsing Title
        expense[count]['Title'] = parseRecord(i, './/nms:Ustrd')

        print(expense[count]['Name'], ' - ', expense[count]['Title'])


loadStatementXML()