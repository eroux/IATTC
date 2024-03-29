import csv
import plotly.graph_objects as go
import pandas as pd
import datetime
from flask import Flask, request
import json
import plotly
import plotly.express as px

app = Flask("plots", static_url_path='', static_folder='web/')

CLUSTERS = {}
EVENTSBYTEXT = {}
DTOIGNORE = {}
PINFO = {}
TEXTINFO = {}
NAMES = {}
DUPLICATENAMES = {}

ROLEEVENTS = {
    "author": "authorship",
    "translator": "translation1",
    "translatorPandita": "translation1",
    "sponsor": "translation1",
    "translator2": "translation2",
    "translator2Pandita": "translation2",
    "revisor": "revision1",
    "revisorpandita": "revision1",
    "revisionsponsor": "revision1",
    "revisor2": "revision2",
    "revisor2pandita": "revision2",
    "revisor3": "revision3",
    "revisor3pandita": "revision3"
}

def add_cluster(p1, p2, cltype, textref):
    key = key = p1+'-'+p2+'-'+cltype
    if cltype == "sync":
        lowestp = p1 if p1 < p2 else p2
        otherp = p2 if p1 < p2 else p1
        key = lowestp+'-'+otherp+'-'+cltype
    if key not in CLUSTERS:
        CLUSTERS[key] = {
            'p1': p1,
            'p2': p2,
            'cltype': cltype,
            'textrefs': set()
        }
    CLUSTERS[key]["textrefs"].add(textref)

def add_clusters(textevents, textref):
    # first simple clusters: people participating in the same event:
    for actorsinfos in textevents.values():
        persons = actorsinfos['actors']
        for i in range(len(persons)):
            for j in range(i, len(persons)):
                add_cluster(persons[i], persons[j], "sync", textref)
    # authors are before translators
    if "authorship" in textevents:
        authors = textevents["authorship"]
        for event, persons in textevents.items():
            if event == "authorship":
                continue
            for p in persons:
                for author in authors:
                    add_cluster(author, p, "before", textref)
    # translators are before revisers and further translators, but after authors
    if "translation1" in textevents:
        translators = textevents["translation1"]
        for event, persons in textevents.items():
            if event == "authorship" or event == "translation1":
                continue
            for p in persons:
                for translator in translators:
                    add_cluster(translator, p, "before", textref)


def clustersFromFile(fname):
    previoustextid = ""
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip first two lines:
        next(reader)
        next(reader)
        for row in reader:
            textid = row[0]
            if textid in DTOIGNORE:
                continue
            role = row[2]
            personid = row[3]
            if personid == "" or '?' in personid or "," in personid or '-' in personid:
                continue
            if role not in ROLEEVENTS:
                continue
            eventtype = ROLEEVENTS[role]
            if textid not in EVENTSBYTEXT:
                EVENTSBYTEXT[textid] = {}
            textevents = EVENTSBYTEXT[textid]
            if eventtype not in textevents:
                textevents[eventtype] = {'actors': []}
            textevents[eventtype]['actors'].append(personid)
            if previoustextid == "":
                previoustextid = textid
            if textid != previoustextid and previoustextid != "":
                # got all the information about an event, add clusters
                add_clusters(EVENTSBYTEXT[previoustextid], previoustextid)
                previoustextid = textid

def get_int_date(s):
    if s == "":
        return None
    try:
        return int(s)
    except:
        return None

def personInfoFromFile(fnamesrc, defaultorigin):
    with open(fnamesrc, newline='') as csvfile:
        rows = []
        reader = csv.reader(csvfile)
        next(reader)
        next(reader)
        seennames = {}
        for row in reader:
            dates = {}
            dates['by'] = get_int_date(row[4])
            dates['flnb'] = get_int_date(row[5])
            dates['flna'] = get_int_date(row[6])
            dates['dy'] = get_int_date(row[7])
            # inferred floruit not before / after
            dates['inflnb'] = 9999
            dates['inflna'] = -9999
            # notbefore max is for calculation with the "after" clusters
            dates['inflnbmax'] = -9999
            dates['inflnamin'] = 9999
            origin = row[9] if row[9] else defaultorigin
            name = ""
            if defaultorigin == "ind" and row[2]:
                name = row[2].split(',')[0].strip().title()
            else:
                name = row[1].split(',')[0].strip(" /")
            if name in seennames:
                DUPLICATENAMES[name] = True
            seennames[name] = True
            PINFO[row[0]] = {"dates": dates, "origin": origin, "name": name}

def infer_dates_cluster(cl):
    p1 = cl['p1']
    p2 = cl['p2']
    cltype = cl['cltype']
    p1dates = PINFO[p1]['dates']
    p2dates = PINFO[p2]['dates']
    p1notbefore = p1dates['by'] if p1dates['by'] is not None else p1dates['flnb']
    p2notbefore = p2dates['by'] if p2dates['by'] is not None else p2dates['flnb']
    p1notafter = p1dates['dy'] if p1dates['dy'] is not None else p1dates['flna']
    p2notafter = p2dates['dy'] if p2dates['dy'] is not None else p2dates['flna']
    if cltype == "after":
        if p1notbefore is not None and p2notbefore is None:
            p2dates['inflnbmax'] = max(p2dates['inflnbmax'], p1notbefore)
        if p2notafter is not None and p1notafter is None:
            p1dates['inflnamin'] = min(p1dates['inflnamin'], p2notafter)
    if cltype == "sync":
        if p1notafter is not None and p2notafter is None:
            p2dates['inflna'] = max(p2dates['inflna'], p1notafter)
        if p2notafter is not None and p1notafter is None:
            p1dates['inflna'] = max(p1dates['inflna'], p2notafter)
        if p1notbefore is not None and p2notbefore is None:
            p2dates['inflnb'] = min(p2dates['inflnb'], p1notbefore)
        if p2notbefore is not None and p1notbefore is None:
            p1dates['inflnb'] = min(p1dates['inflnb'], p2notbefore)

def infer_dates():
    # start with sync clusters:
    for cluster in CLUSTERS.values():
        if cluster['p1'] not in PINFO or cluster['p2'] not in PINFO:
            print("warning: %s or %s not in persons sheet" % (cluster['p1'], cluster['p2']))
            continue
        if cluster["cltype"] == "sync":
            infer_dates_cluster(cluster)
    # then the after types
    for cluster in CLUSTERS.values():
        if cluster['p1'] not in PINFO or cluster['p2'] not in PINFO:
            print("warning: %s or %s not in persons sheet" % (cluster['p1'], cluster['p2']))
            continue
        if cluster["cltype"] == "after":
            infer_dates_cluster(cluster)

def add_text_info():
    with open("../../csv/sametexts.txt", newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            DTOIGNORE[row[0]] = True
    with open("../../csv/textdata.csv", newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row[0] not in DTOIGNORE:
                TEXTINFO[row[0]] = {'section': row[1], 'nbpages': int(row[2])}

def intersection_years(plist):
    nb = -9999
    na = 9999
    for p in plist:
        if not p in PINFO:
            continue
        dates = PINFO[p]['dates']
        if dates['by'] is not None:
            nb = max(nb, dates['by'] + 15)
        elif dates['flnb'] is not None:
            nb = max(nb, dates['flnb'])
        elif dates['inflnb'] is not None and dates['inflnb'] != 9999:
            nb = max(nb, dates['inflnb'])
        if dates['dy'] is not None:
            na = min(na, dates['dy'])
        elif dates['flna'] is not None:
            na = min(na, dates['flna'])
        elif dates['inflna'] is not None and dates['inflna'] != -9999:
            na = min(na, dates['inflna'])
    if na != 9999 and nb != -9999:
        return [na, nb]
    return None

def mean_year(plist, base=25):
    intersect = intersection_years(plist)
    if intersect is None:
        return None
    return int(intersect[0]+(intersect[1]-intersect[0])/2)

def add_missing_events():
    for textid in TEXTINFO:
        hasauthorship = textid > "D1108"
        if textid not in EVENTSBYTEXT:
            EVENTSBYTEXT[textid] = {'translation1': 'unknown'}
            if hasauthorship:
                EVENTSBYTEXT[textid]['authorship'] = 'unknown'
        else:
            if 'translation1' not in EVENTSBYTEXT[textid]:
                EVENTSBYTEXT[textid]['translation1'] = 'unknown'
            if hasauthorship and 'authorship' not in EVENTSBYTEXT[textid]:
                EVENTSBYTEXT[textid]['authorship'] = 'unknown'

def plot_events_by_date(sectionlist, counttype, eventtypelist, name):
    eventsbydate = {}
    noinfocount = 0
    nodatecount = 0
    for textid, textevents in EVENTSBYTEXT.items():
        if textid not in TEXTINFO:
            # quite a bizarre case...
            print("textid not in textinfo: "+textid)
            continue
        textinfo = TEXTINFO[textid]
        for eventtype, eventinfo in textevents.items():
            if 'all' not in eventtypelist and eventtype not in eventtypelist:
                continue
            if 'all' not in sectionlist and textinfo['section'] not in sectionlist:
                continue
            count = 1 if counttype == "T" else textinfo['nbpages']
            if eventinfo == "unknown":
                noinfocount += count
                continue
            year = mean_year(eventinfo['actors'])
            if year is None:
                nodatecount += count
                continue
            if year > 2000:
                print("year > 2000", textid, eventinfo['actors'])
            date = "{1:0{0}d}-01-01".format(4 if year >= 0 else 5, year)
            if date not in eventsbydate:
                eventsbydate[date] = 0
            eventsbydate[date] += count
    eventsbydate["0100-01-01"] = noinfocount
    eventsbydate["0125-01-01"] = nodatecount
    dates = sorted(eventsbydate.keys())
    values = []
    for d in dates:
        values.append(eventsbydate[d])
    fig = go.Figure()
    df = pd.DataFrame(dict(
        date=dates,
        value=values
    ))
    fig.add_trace(go.Bar(
        x=df["date"], y=df["value"],
        xperiod="M300",
        xperiodalignment="middle",
        name=name
    ))
    fig.update_xaxes(showgrid=True, ticklabelmode="period", dtick="M600", tickformat="%Y")
    fig.update_layout(xaxis_range=[datetime.datetime(100, 10, 17),
                               datetime.datetime(1800, 11, 20)])
    return fig

def plot_events_by_person(sectionlist, counttype, eventtypelist, name):
    eventsbyperson = {"unknown": 0}
    for textid, textevents in EVENTSBYTEXT.items():
        if textid not in TEXTINFO:
            # quite a bizarre case...
            print("textid not in textinfo: "+textid)
            continue
        textinfo = TEXTINFO[textid]
        for eventtype, eventinfo in textevents.items():
            if 'all' not in eventtypelist and eventtype not in eventtypelist:
                continue
            if 'all' not in sectionlist and textinfo['section'] not in sectionlist:
                continue
            count = 1 if counttype == "T" else textinfo['nbpages']
            if eventinfo == "unknown":
                eventsbyperson["unknown"] += count
                continue
            for p in eventinfo['actors']:
                if p not in PINFO:
                    continue
                if p not in eventsbyperson:
                    eventsbyperson[p] = 0
                eventsbyperson[p] += count
    # sort p by count descending
    ps = sorted(eventsbyperson.keys(), key=lambda p: eventsbyperson[p], reverse=True)
    values = []
    names = []
    for p in ps:
        values.append(eventsbyperson[p])
        if p == "unknown":
            names.append("unknown")
        else:
            n = PINFO[p]['name']
            if n in DUPLICATENAMES:
                names.append(n+" ("+p+")")
            else:
                names.append(n)        
    fig = go.Figure()
    df = pd.DataFrame(dict(
        name=names,
        value=values
    ))
    fig.add_trace(go.Bar(
        x=df["name"], y=df["value"],
        name=name
    ))
    return fig

# TODO:
# plot by number of persons involved
# plot origin of persons
# plot known vs. unknown
# plot nb of texts worked on by person, with a top 100

INIT = False
def init():
    global INIT
    if INIT:
        return
    add_text_info()
    clustersFromFile("../../csv/DergeTengyur.csv")
    clustersFromFile("../../csv/DergeKangyur.csv")
    personInfoFromFile("../../csv/Persons-Ind.csv", "ind")
    personInfoFromFile("../../csv/Persons-Tib.csv", "tib")
    infer_dates()
    add_missing_events()
    INIT = True

SECTION_MAPPING = {
    "mdo 'grel (general)": ["mdo 'grel (sher phyin)", "mdo 'grel (dbu ma)", "mdo 'grel (mdo)", "mdo 'grel (sems tsam)", "mdo 'grel (mngon pa)", "mdo 'grel (skyes rabs)", "mdo 'grel (spring yig)", "mdo 'grel (tshad ma)", "mdo 'grel (sgra mdo)", "mdo 'grel (gso rig)", "mdo 'grel (bzo rig)", "mdo 'grel (thun mong ba lugs kyi bstan bcos)", "mdo 'grel (bstan bcos sna tshogs)"],
    "mdo (general)": ["'bum", "nyi khri", "khri brgyad", "khri pa", "brgyad stong", "sher phyin", "phal chen", "dkon brtsegs", "mdo sde"],
    "rgyud (general)": ["rgyud", "rnying rgyud", "gzungs", "dus 'khor"]
}

EVENTTYPE_MAPPING = {
    "translation": ["translation1", "translation2", "translation3"],
    "revision": ["revision1", "revision2", "revision3"],
}

@app.route('/plotjson', methods=['GET'])
def plotjson():
    init()
    args = request.args.to_dict()
    graphtype = "time"
    if "graphtype" in args:
        graphtype = args["graphtype"]
    sectionlist = ['all']
    name = ""
    if "section" in args:
        name += args["section"]
        sectionlist = args["section"].split(",")
        toadd = []
        for s in sectionlist:
            if s in SECTION_MAPPING:
                toadd += SECTION_MAPPING[s]
        sectionlist += toadd
    else:
        print("section not in args!")
    eventtypelist = ["all"]
    if "eventtype" in args:
        name += ", "+ args["eventtype"]
        eventtypelist = args["eventtype"].split(",")
        toadd = []
        for s in eventtypelist:
            if s in EVENTTYPE_MAPPING:
                toadd += EVENTTYPE_MAPPING[s]
        eventtypelist += toadd
    count = "T"
    if "count" in args:
        count = args["count"]
    name += ", "+ count
    fig = None
    if graphtype == "byperson":
        fig = plot_events_by_person(sectionlist, count, eventtypelist, name)
    else:
        fig = plot_events_by_date(sectionlist, count, eventtypelist, name)
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder) 

@app.route('/', methods=['GET'])
def default():
    return app.send_static_file('demo.html')

def main():
    init()

if __name__ == '__main__':
    init()
    roles = {"total": set()}
    origins = {"total": set()}
    new = {"total": set()}
    withdates = {"known": set(), "fl": set(), "infl": set()}
    for textid, textevents in EVENTSBYTEXT.items():
        if textid not in TEXTINFO:
            # quite a bizarre case...
            print("textid not in textinfo: "+textid)
            continue
        textinfo = TEXTINFO[textid]
        for eventtype, eventinfo in textevents.items():
            if eventinfo == "unknown":
                continue
            for p in eventinfo['actors']:
                if p not in PINFO:
                    continue
                if eventtype not in roles:
                    roles[eventtype] = set()
                    new[eventtype] = set()
                roles[eventtype].add(p)
                pinfo = PINFO[p]
                if pinfo['origin'] not in origins:
                    origins[pinfo['origin']] = set()
                origins[pinfo['origin']].add(p)
                origins["total"].add(p)
                roles["total"].add(p)
                if "AT" in p:
                    new[eventtype].add(p)
                    new["total"].add(p)
                if pinfo["dates"]["by"] is not None or pinfo["dates"]["dy"] is not None:
                    withdates["known"].add(p)
                elif pinfo["dates"]["flnb"] is not None and pinfo["dates"]["flna"] is not None:
                    withdates["fl"].add(p)
                elif pinfo["dates"]["inflnb"] != 9999 and pinfo["dates"]["inflna"] != -9999:
                    withdates["infl"].add(p)
    for role, ps in roles.items():
        print("%s: %d" % (role, len(ps)))
    for origin, ps in origins.items():
        print("%s: %d" % (origin, len(ps)))
    for origin, ps in new.items():
        print("%s: %d" % (origin, len(ps)))
    for origin, ps in withdates.items():
        print("%s: %d" % (origin, len(ps)))


# run with 
# FLASK_APP=plots flask run -p 5001