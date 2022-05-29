import csv
from xml.etree.ElementTree import ElementTree
import sys
import re

RKTSTOD = {}

P = re.compile(r'^(?P<sf>\d+)(?P<sab>[ab])\d?-(?P<ef>\d+)(?P<eab>[ab])\d?$')

def getnbpages(rktspstr):
    m = P.search(rktspstr)
    if m is None:
        print("can't understand "+rktspstr)
        return None
    start = 2*int(m.group("sf")) - (1 if m.group("sab") == "a" else 0)
    end = 2*int(m.group("ef")) - (1 if m.group("eab") == "a" else 0)
    return (end - start)+1


def extractfromfile(filename, res):
    doc = ElementTree()
    doc.parse(filename)
    outline = doc.getroot()
    for item in outline.findall('item'):
        ref = item.find('ref').text
        nbpages = None
        section = None
        for loc in item.findall("loc"):
            if loc.find("set").text in ["MW23703", "MW4CZ5369"]:
                vol = loc.find("vol").text
                section = vol.split(",")[0]
                locnbpages = getnbpages(loc.find("p").text)
                if nbpages is None:
                    nbpages = 0
                nbpages += locnbpages
        if nbpages is None:
            print("can't find nbpages in "+ref)
        else:
            print(ref+","+section+","+str(nbpages))

extractfromfile("../csv/D.xml", None)
extractfromfile("../csv/DT.xml", None)
#print(getnbpages("127a2-127b7"))