import hashlib
import io
import os
from pathlib import Path
from rdflib import URIRef, Literal, BNode, Graph, ConjunctiveGraph
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD
import csv

GITPATH = "../../persons/"

BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")
TMP = Namespace("http://purl.bdrc.io/ontology/tmp/")
BDA = Namespace("http://purl.bdrc.io/admindata/")
ADM = Namespace("http://purl.bdrc.io/ontology/admin/")

NSM = NamespaceManager(Graph())
NSM.bind("bdr", BDR)
NSM.bind("bdo", BDO)
NSM.bind("tmp", TMP)
NSM.bind("bda", BDA)
NSM.bind("adm", ADM)
NSM.bind("skos", SKOS)
NSM.bind("rdfs", RDFS)

def get_csv(path):
    res = []
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
           res.append(row) 
    return res

def write_csv(path, rows):
    with open(path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

def labelsforpath(pFilePath):
    # if file name is the same as an image instance already present in the database, don't read file:
    p = BDR[Path(pFilePath).stem]
    model = ConjunctiveGraph()
    model.parse(str(pFilePath), format="trig")
    res = {}
    for _, _, o in model.triples( (p, SKOS.prefLabel, None) ):
        res[o.language] = o.value
    return res

def onefile(csvpath):
    rows = get_csv(csvpath)
    for row in rows[1:]:
        rid = row[0]
        if "TMP" in rid:
            continue
        md5 = hashlib.md5(str.encode(rid))
        two = md5.hexdigest()[:2]
        modelpath = GITPATH+'/'+two+'/'+rid+'.trig'
        labels = labelsforpath(modelpath)
        for l in ["bo-x-ewts", "sa-x-iast", "sa-x-ewts", "sa-x-ndia"]:
            if l in labels:
                row[1] = labels[l]
                break
    write_csv(csvpath, rows)

def main():
    onefile("../csv/Persons-Tib.csv")
    #onefile("../csv/Persons-Ind.csv")

#mainIiif("W1PD166109")
main()


