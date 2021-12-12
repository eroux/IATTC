import csv
import rdflib
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD, URIRef
from rdflib.term import Literal

BF = Namespace("http://id.loc.gov/ontologies/bibframe/")
BDR = Namespace("http://purl.bdrc.io/resource/")
BDO = Namespace("http://purl.bdrc.io/ontology/core/")
TMP = Namespace("http://purl.bdrc.io/ontology/tmp/")
BDG = Namespace("http://purl.bdrc.io/graph/")
BDA = Namespace("http://purl.bdrc.io/admindata/")
ADM = Namespace("http://purl.bdrc.io/ontology/admin/")
MBBT = Namespace("http://mbingenheimer.net/tools/bibls/")
CBCT_URI = "https://dazangthings.nz/cbc/text/"
CBCT = Namespace(CBCT_URI)

NSM = NamespaceManager(rdflib.Graph())
NSM.bind("bdr", BDR)
NSM.bind("", BDO)
NSM.bind("bdg", BDG)
NSM.bind("bda", BDA)
NSM.bind("adm", ADM)
NSM.bind("skos", SKOS)
NSM.bind("rdf", RDF)
NSM.bind("cbct", CBCT)
NSM.bind("mbbt", MBBT)
NSM.bind("bf", BF)

x = rdflib.term._toPythonMapping.pop(rdflib.XSD['gYear'])

adm = BDA.ADATII

def import_persons(fname, reg):
    global adm
    with open(fname,  newline='') as csvfile:
        srcreader = csv.reader(csvfile, delimiter=',')
        next(srcreader)
        next(srcreader)
        for row in srcreader:
            if not row[0].startswith("P0AT"):
                continue
            p = BDR[row[0]]
            reg.add((p, RDF.type, BDO.Person))
            reg.add((adm, ADM.adminAbout, p))
            if row[1] != "":
                i = 0
                for tn in row[1].split(","):
                    tn = tn.strip()
                    if i == 0:
                        reg.add((p, SKOS.prefLabel, Literal(tn, lang="bo-x-ewts")))
                    n = BDR["NM"+row[0]+"T"+str(i)]
                    reg.add((n, RDFS.label, Literal(tn, lang="bo-x-ewts")))
                    reg.add((n, RDF.type, BDO.PersonPrimaryTitle))
                    reg.add((p, BDO.personName, n))
                    i += 1
            if row[2] != "":
                i = 0
                for indn in row[2].split(","):
                    indn = indn.strip()
                    if i == 0:
                        reg.add((p, SKOS.prefLabel, Literal(indn, lang="sa-x-iast")))
                    n = BDR["NM"+row[0]+"I"+str(i)]
                    reg.add((n, RDFS.label, Literal(indn, lang="sa-x-iast")))
                    reg.add((n, RDF.type, BDO.PersonPrimaryTitle))
                    reg.add((p, BDO.personName, n))
                    i += 1
            if row[4] != "":
                try:
                    year = "%04d" % int(row[4])
                    n = BDR["EV"+row[0]+"B"]
                    reg.add((n, RDF.type, BDO.PersonBirth))
                    reg.add((n, BDO.onYear, Literal(year, datatype=XSD.gYear)))
                    reg.add((p, BDO.personEvent, n))
                except:
                    pass
            if row[7] != "":
                try:
                    year = "%04d" % int(row[7])
                    n = BDR["EV"+row[0]+"B"]
                    reg.add((n, RDF.type, BDO.PersonDeath))
                    reg.add((n, BDO.onYear, Literal(year, datatype=XSD.gYear)))
                    reg.add((p, BDO.personEvent, n))
                except:
                    pass
            floruit = None
            if row[5] != "":
                try:
                    year = "%04d" % int(row[5])
                    floruit = BDR["EV"+row[0]+"F"]
                    reg.add((floruit, RDF.type, BDO.PersonFlourished))
                    reg.add((floruit, BDO.notBefore, Literal(year, datatype=XSD.gYear)))
                    reg.add((p, BDO.personEvent, floruit))
                except:
                    pass
            if row[6] != "":
                try:
                    year = "%04d" % int(row[6])
                    if floruit is None:
                        floruit = BDR["EV"+row[0]+"F"]
                        reg.add((floruit, RDF.type, BDO.PersonFlourished))
                        reg.add((p, BDO.personEvent, floruit))
                    reg.add((floruit, BDO.notAfter, Literal(year, datatype=XSD.gYear)))
                except:
                    pass

reg = rdflib.Graph()
reg.parse("static.ttl", format="turtle")
import_persons("../csv/Persons-Ind.csv", reg)
import_persons("../csv/Persons-Tib.csv", reg)

reg.serialize("ATII.ttl", format="turtle")

# curl -X PUT -H Content-Type:text/turtle -T ATII.ttl -G http://buda1.bdrc.io:13180/fuseki/corerw/data --data-urlencode 'graph=http://purl.bdrc.io/graph/ATII'