#! python 3

from os import name
import xml.etree.ElementTree as ET


class transaction:

    def __init__(self) -> None:
        pass






def loadStatementXML():

    tree = ET.parse('statement.xml')
    root = tree.getroot()
    namespace = {'nms':'urn:iso:std:iso:20022:tech:xsd:camt.053.001.06'}

    print(len(root.findall('.//nms:Ntry', namespace)))
    #for n in root.findall('.//nms:Ntry', namespace):
     #   print(n.tag)

    for n in root.findall('.//nms:Ntry', namespace):
        print(len(n.findall('.//nms:Nm', namespace)))
        Name = n.findall('nms:Nm', namespace)
        print(Name)
        pass

loadStatementXML()