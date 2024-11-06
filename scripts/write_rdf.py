import csv
import rdflib
from rdflib.namespace import RDF, RDFS, SKOS, OWL, Namespace, NamespaceManager, XSD, URIRef
from rdflib import Literal, Graph, Dataset
import re
import hashlib
import random
import string
from datetime import datetime
import sys
from pathlib import Path
import os

GIT_ROOT = "../../../tbrc-ttl/"
if len(sys.argv) > 1:
    GIT_ROOT = sys.argv[1]
GIT_REPO_SUFFIX = "-20220922"

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
EDTF = Namespace("http://id.loc.gov/datatypes/edtf/")

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
NSM.bind("edtf", EDTF)

def bind_prefixes(g):
    g.bind("bdr", BDR)
    g.bind("bdo", BDO)
    g.bind("bda", BDA)
    g.bind("bdg", BDG)
    g.bind("bf", BF)
    g.bind("adm", ADM)
    g.bind("skos", SKOS)
    g.bind("owl", OWL)
    g.bind("rdf", RDF)
    g.bind("rdfs", RDFS)
    g.bind("edtf", EDTF)

x = rdflib.term._toPythonMapping.pop(rdflib.XSD['gYear'])

INFERRED = {}

def save_file(ds, main_lname):
    md5 = hashlib.md5(str.encode(main_lname))
    two = md5.hexdigest()[:2]
    repo = get_repo(main_lname)
    filepathstr = GIT_ROOT+repo+GIT_REPO_SUFFIX+"/"+two+"/"+main_lname+".trig"
    print(os.path.abspath(filepathstr))
    #ds.serialize(filepathstr, format="trig")

def get_random_id(length = 12):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

NOW_LIT = Literal(datetime.now().isoformat(), datatype=XSD.dateTime)
LGE = BDA["LG0BDS"+get_random_id()]

def add_lge(g, adm):
    g.add((adm, ADM.logEntry, LGE))
    g.add((LGE, RDF.type, ADM.UpdateData))
    g.add((LGE, ADM.logAgent, Literal("IATTC/scripts/write_rdf.py")))
    g.add((LGE, ADM.logMethod, BDA.BatchMethod))
    g.add((LGE, ADM.logDate, NOW_LIT))
    g.add((LGE, ADM.logMessage, Literal("import data from the ATII project", lang="en")))

def get_repo(rid):
    if rid.startswith("P"):
        return "persons"
    elif rid.startswith("WA"):
        return "works"

def get_ds(e):
    md5 = hashlib.md5(str.encode(e))
    two = md5.hexdigest()[:2]
    repo = get_repo(e)
    filepathstr = GIT_ROOT+repo+GIT_REPO_SUFFIX+"/"+two+"/"+e+".trig"
    ds = Dataset()
    if Path(filepathstr).is_file():
        ds.parse(filepathstr, format="trig", publicID=BDG[e])
    bind_prefixes(ds)
    return ds

def get_graph_names(g, langtagstart):
    res = []
    for _, _, pl in g.triples((None, SKOS.prefLabel, None)):
        if pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")):
            res.append(str(pl))
    for _, _, pl in g.triples((None, SKOS.altLabel, None)):
        if pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")):
            res.append(str(pl))
    for _, _, pl in g.triples((None, RDFS.label, None)):
        if (pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")) ) and str(pl) not in res:
            res.append(str(pl))
    # we keep the first element first and sort the rest
    if len(res) > 2:
        res = [res[0]] + sorted(res[1:])
    return res

EVTTYPEURITOKEY = {
    "http://purl.bdrc.io/ontology/core/PersonBirth": "PersonBirth",
    "http://purl.bdrc.io/ontology/core/PersonDeath": "PersonDeath",
    "http://purl.bdrc.io/ontology/core/PersonFlourished": "PersonFlourished"
}

def get_graph_events(g):
    res = {}
    for evt, _, evtwhen in g.triples((None, BDO.eventWhen, None)):
        evttype = g.value(evt, RDF.type)
        if str(evttype) in EVTTYPEURITOKEY:
            key = EVTTYPEURITOKEY[str(evttype)]
            res[key] = evtwhen
    return res

def replace_names(g, lname, langtagstart, langtag, nameslist):
    # first name as prefLabel, others as OtherName
    to_remove = []
    for s, _, pl in g.triples((None, SKOS.prefLabel, None)):
        if pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")):
            to_remove.append((s, SKOS.prefLabel, pl))
    for s, _, pl in g.triples((None, SKOS.altLabel, None)):
        if pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")):
            to_remove.append((s, SKOS.altLabel, pl))
    for n, _, pl in g.triples((None, RDFS.label, None)):
        if pl.language.startswith(langtagstart) or (langtagstart == "bo" and pl.language.endswith("ewts")):
            for s2, p2, o2 in g.triples((n, None, None)):
                to_remove.append((s2, p2, o2))
            for s2, p2, o2 in g.triples((None, None, n)):
                to_remove.append((s2, p2, o2))
    for t in to_remove:
        g.remove(t)
    if not nameslist:
        return
    g.add((BDR[lname], SKOS.prefLabel, Literal(nameslist.pop(0), lang=langtag)))
    for i, name in enumerate(nameslist):
        n = BDR["NM"+lname+"_ATII_"+langtag+str(i)]
        g.add((BDR[lname], BDO.personName, n))
        g.add((n, RDF.type, BDO.PersonOtherName))
        g.add((n, RDFS.label, Literal(name, lang=langtag)))

def replace_events(g, lname, events):
    to_remove = []
    for evt, _, evtwhen in g.triples((None, BDO.eventWhen, None)):
        evttype = evt.value(evt, RDF.type)
        if str(evttype) in EVTTYPEURITOKEY:
            for s2, p2, o2 in g.triples((evt, None, None)):
                to_remove.append((s2, p2, o2))
            for s2, p2, o2 in g.triples((None, None, evt)):
                to_remove.append((s2, p2, o2))
    for evtkey, when in events.items():
        evt = BDR["EV"+lname+"_ATII_"+evtkey[0]]
        g.add((BDR[lname], BDO.personEvent, evt))
        g.add((evt, RDF.personEvent, BDO[evtkey]))
        g.add((evt, BDO.eventWhen, Literal(when, datatype=EDTF.EDTF)))


def get_diff(graph, row):
    """
    First get the graph data and row data both in the following form:
    {
       "sa_names": [...],
       "bo_name": [...],
       "birth": "...",
       "death": "...",
       "floruit": "..."
    }

    Then returns the diff in the form:

    """
    return

def get_names(names_str, replaceX=False):
    res = [x.strip() for x in names_str.split(',')]
    if replaceX:
        res = [x.replace("X", "**") for x in res]
    if len(res) > 2:
        res = [res[0]] + sorted(res[1:])
    return res

def log_replacement(p, type, old, new):
    if "AT" in p:
        return
    print(f"{p}: replacing {type} from {old} to {new}")

def import_persons(fname, reg):
    global adm
    with open(fname,  newline='') as csvfile:
        srcreader = csv.reader(csvfile, delimiter=',')
        next(srcreader)
        next(srcreader)
        for row in srcreader:
            ds = get_ds(row[0])
            g = ds.graph(BDG[row[0]])
            p = BDR[row[0]]
            sa_names = get_names(row[2], replaceX=True)
            bo_names = get_names(row[1])
            print(bo_names)
            events = {}
            if row[4] != "":
                events["PersonBirth"] = row[4].strip()
            if row[7] != "":
                events["PersonDeath"] = row[7].strip()
            floruit = ""
            if row[5] != "":
                floruit = row[5].strip()
            if row[6] != "":
                floruit += "/"+row[6].strip()
            if floruit:
                events["PersonFlourished"] = floruit
            needsWriting = False
            if sa_names != get_graph_names(g, "sa"):
                needsWriting = True
                replace_names(g, row[0], "sa", "sa-x-iast", sa_names)
                log_replacement(row[0], "Sanskrit names", get_graph_names(g, "sa"), sa_names)
            if bo_names != get_graph_names(g, "bo"):
                needsWriting = True
                replace_names(g, row[0], "bo", "bo-x-ewts", bo_names)
                log_replacement(row[0], "Tibetan names", get_graph_names(g, "bo"), bo_names)
            if events != get_graph_events(g):
                needsWriting = True
                replace_names(g, row[0], "bo", "bo-x-ewts", bo_names)
                log_replacement(row[0], "Events", get_graph_events(g), events)
            if needsWriting:
                add_lge(g, BDA[row[0]])
                save_file(ds, row[0])
            #if len(row) > 18 and row[19] == "F":
            #    reg.add((p, BDO.personGender, BDR.GenderFemale))

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