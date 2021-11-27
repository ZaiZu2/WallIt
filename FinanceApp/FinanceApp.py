#! python 3

from os import name
import xml.etree.ElementTree as ET


class transaction:

    def __init__(self) -> None:
        pass






def loadStatementXML(): #parsing an XML monthly bank account statement
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
            value.append(rootObj.find(XPath, namespace).get('Ccy'))
        except AttributeError:
            value = None
        return value

    tree = ET.parse('statement.xml')
    root = tree.getroot()
    namespace = {'nms':'urn:iso:std:iso:20022:tech:xsd:camt.053.001.06'}

    expenses = []
    record = {'Name': None, 'Title': None, 'Dir': None, 'Amount': [], 'SrcAmount': [], 'Date': None, 'Place': None}

    for count, i in enumerate(root.findall('.//nms:Ntry', namespace)): # Parsing expense records
        expenses.append(record)

        expenses[count]['Name'] = parseRecord(i, './/nms:RltdPties//nms:Nm')
        expenses[count]['Title'] = parseRecord(i, './/nms:Ustrd')

        expenses[count]['Dir'] = parseRecord(i, './nms:CdtDbtInd') # Parsing just 'DBIT' or 'CRDT' to dictionary
        if expenses[count]['Dir'] == 'Dbit':
            expenses[count]['Dir'] = -1
        else:
            expenses[count]['Dir'] = 1

        expenses[count]['Amount'] = parseAmount(i, './nms:Amt') # Parses array [Amount, Currency]
        expenses[count]['SrcAmount'] = parseAmount(i, './/nms:InstdAmt/nms:Amt') # Parses array [Amount, Currency]
 
        expenses[count]['Date'] = parseRecord(i, './/nms:BookgDt/nms:Dt')
        expenses[count]['Place'] = parseRecord(i, './/nms:PstlAdr/nms:TwnNm')
        print(expenses[count])

    #print('\n')
    #for expense in expenses:
    #    print(expense)


    #summary = root.findall('.//nms:TxsSummry', namespace) # Check if expenses add up to correct sum
    IncSum = 0

    for i, expense in enumerate(expenses):

        pass
        
        #print(expenses[i]['Dir']*expenses[i]['Amount'][0], IncSum)
        #IncSum += expense['Dir'] * expense['Amount'][0]
        #print(IncSum)
    if IncSum != root.find('.//nms:TtlCdtNtries/nms:Sum', namespace).text: # = IncSum
        print('Cos jest niehalo')
        print(IncSum)


loadStatementXML()