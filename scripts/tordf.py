import csv
import rdflib
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD, URIRef
from rdflib.term import Literal
import re

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

INFERRED = {}

adm = BDA.ADATII

def import_persons(fname, reg):
    global adm
    with open(fname,  newline='') as csvfile:
        srcreader = csv.reader(csvfile, delimiter=',')
        next(srcreader)
        next(srcreader)
        for row in srcreader:
            p = BDR[row[0]]
            if not row[0].startswith("P0AT"):
                # we add the Sanskrit names for records already on BDRC
                if row[2] != "":
                    i = 0
                    for indn in row[2].split(","):
                        i += 1
                        indn = indn.strip()
                        n = BDR["NM"+row[0]+"I"+str(i)]
                        reg.add((n, RDFS.label, Literal(indn, lang="sa-x-iast")))
                        reg.add((n, RDF.type, BDO.PersonPrimaryTitle))
                        reg.add((p, BDO.personName, n))
                continue
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
            if len(row) > 18 and row[19] == "F":
                reg.add((p, BDO.personGender, BDR.GenderFemale))

reg = rdflib.Graph()
reg.parse("static.ttl", format="turtle")

def add_infer(fname):
    global INFERRED
    with open(fname,  newline='') as csvfile:
        srcreader = csv.reader(csvfile, delimiter=',')
        for row in srcreader:
            if row[1]:
                INFERRED[row[0]] = row[1]

add_infer('../csv/Persons-Ind-withinfer.csv')
add_infer('../csv/Persons-Tib-withinfer.csv')

import_persons("../csv/Persons-Ind.csv", reg)
import_persons("../csv/Persons-Tib.csv", reg)

DTORKTS = {}
with open('../csv/derge-rkts.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        DTORKTS[row[1]] = row[0]

RKTSTOWAI = {}
with open('../csv/abstract-rkts.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        if "?" in row[1]:
            continue
        RKTSTOWAI[row[1]] = row[0]

ROLEMAPPING = {
    "author": BDR.R0ER0019,
    "translator": BDR.R0ER0026,
    "pandita": BDR.R0ER0018,
    "sponsor": BDR.R0ER0030,
    "scribe": BDR.R0ER0031,
    "translator2": BDR.R0ER0026, # missing 2
    "pandita2": BDR.R0ER0018, # missing 2
    "revisor": BDR.R0ER0023, # ?
    "revisorPandita": BDR.R0ER0018, # ?
    "revisionsponsor": BDR.R0ER0030, # ?
    "revisor2": BDR.R0ER0023, # ?
    "revisor2pandita": BDR.R0ER0018, # ?
    "revisor3": BDR.R0ER0023, # ?
    "revisor3pandita": BDR.R0ER0018, # ?
    "requesterOfTranslation": BDR.R0ER0028,
}

ROLEEVENTS = {
    "translator2": BDO.SecondTranslatedEvent,
    "pandita2": BDO.SecondTranslatedEvent,
    "revisor": BDO.RevisedEvent,
    "revisorPandita": BDO.RevisedEvent,
    "revisionsponsor": BDO.RevisedEvent,
    "revisor2": BDO.SecondRevisedEvent,
    "revisor2pandita": BDO.SecondRevisedEvent,
    "revisor3": BDO.ThirdRevisedEvent,
    "revisor3pandita": BDO.ThirdRevisedEvent,
}

def import_attributions(fname):
    with open(fname,  newline='') as csvfile:
        srcreader = csv.reader(csvfile, delimiter=',')
        next(srcreader)
        next(srcreader)
        texti = 1
        textevents = {}
        previoustextid = None
        for row in srcreader:
            d = row[0]
            if not d.startswith("D") or d.startswith("Dx"):
                continue
            d = re.sub("D0+", "D", d)
            if not d in DTORKTS:
                print("%s not in rkts!" % d)
                continue
            rkts = DTORKTS[d]
            if row[2] not in ROLEMAPPING:
                continue
            if (not row[3].startswith("P")) or " " in row[3] or "?" in row[3]:
                continue
            if d == previoustextid:
                texti += 1
            else:
                previoustextid = d
                texti = 1
                textevents = {}
            role = ROLEMAPPING[row[2]]
            eventtype = None if row[2] not in ROLEEVENTS else ROLEEVENTS[row[2]]
            watiblname = "WA0R%s%04d" % (rkts[:1], int(rkts[1:]))
            watib = BDR[watiblname]
            waindlname = "WA0R%sI%04d" % (rkts[:1], int(rkts[1:]))
            waind = BDR[waindlname]
            if rkts in RKTSTOWAI:
                waind = BDR[RKTSTOWAI[rkts]]
            aac = BDR["CR"+watiblname+("_%02d" % texti)]
            reg.add((aac, RDF.type, BDO.AgentAsCreator))
            reg.add((aac, BDO.role, role))
            reg.add((aac, BDO.agent, BDR[row[3]]))
            reg.add((watib, BDO.creator, aac))
            if eventtype:
                reg.add((aac, BDO.creationEventType, eventtype))
            if role == BDR.R0ER0019:
                reg.add((waind, BDO.creator, aac))


import_attributions("../csv/DergeKangyur.csv")
import_attributions("../csv/DergeTengyur.csv")

reg.serialize("ATII.ttl", format="turtle")

# curl -X PUT -H Content-Type:text/turtle -T ATII.ttl -G http://buda1.bdrc.io:13180/fuseki/corerw/data --data-urlencode 'graph=http://purl.bdrc.io/graph/ATII'