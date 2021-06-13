import csv

CLUSTERS = {}
DATES = {}

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
    for persons in textevents.values():
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
    textevents = {}
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip first two lines:
        next(reader)
        next(reader)
        for row in reader:
            textid = row[0]
            role = row[2]
            personid = row[3]
            if personid == "" or '?' in personid or "," in personid or '-' in personid:
                continue
            if role not in ROLEEVENTS:
                continue
            event = ROLEEVENTS[role]
            if textid != previoustextid:
                # got all the information about an event, add clusters
                add_clusters(textevents, previoustextid)
                textevents = {}
                previoustextid = textid
            if event not in textevents:
                textevents[event] = []
            textevents[event].append(personid)

def datesFromFile(fname):
    previoustextid = ""
    textevents = {}
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip first two lines:
        next(reader)
        next(reader)
        for row in reader:
            textid = row[0]
            role = row[2]
            personid = row[3]
            if personid == "" or '?' in personid or "," in personid:
                continue
            if role not in ROLEEVENTS:
                continue
            event = ROLEEVENTS[role]
            if textid != previoustextid:
                # got all the information about an event, add clusters
                add_clusters(textevents, textid)
                textevents = {}
                previoustextid = textid
            if event not in textevents:
                textevents[event] = []
            textevents[event].append(personid)

def get_int_date(s):
    if s == "":
        return None
    try:
        return int(s)
    except:
        return None

def datesFromFile(fnamesrc):
    with open(fnamesrc, newline='') as csvfile:
        rows = []
        reader = csv.reader(csvfile)
        next(reader)
        next(reader)
        for row in reader:
            dates = {}
            dates['by'] = get_int_date(row[4])
            dates['flnb'] = get_int_date(row[5])
            dates['flna'] = get_int_date(row[6])
            dates['dy'] = get_int_date(row[7])
            # inferred floruit not before / after
            dates['inflnb'] = None
            dates['inflna'] = None
            DATES[row[0]] = dates

def check_dates_compatible(p1, p1dates, p2, p2dates, cltype, textrefs):
    p1notbefore = p1dates['by'] if p1dates['by'] is not None else p1dates['flnb']
    p2notbefore = p2dates['by'] if p2dates['by'] is not None else p2dates['flnb']
    p1notafter = p1dates['dy'] if p1dates['dy'] is not None else p1dates['flna']
    p2notafter = p2dates['dy'] if p2dates['dy'] is not None else p2dates['flna']
    # in all cases, p1notbefore must be before p2notafter:
    if p1notbefore is not None and p2notafter is not None and p1notbefore >= p2notafter:
        print("error: %s (%d-...) cannot have worked %s %s (...-%d) on %s" % (p1, p1notbefore, "with" if cltype == "sync" else "before", p2, p2notafter, ','.join(textrefs)))
        return False
    # if not in the "before" type, p1notafter must be after p2notbefore:
    if cltype != "before" and p2notbefore is not None and p1notafter is not None and p2notbefore >= p1notafter:
        print("error: %s (...-%d) cannot have worked with %s (%d-...) on %s" % (p1, p1notafter, p2, p2notbefore, ','.join(textrefs)))
        return False
    return True

def check_clusters_coherence():
    for cluster in CLUSTERS.values():
        if cluster['p1'] not in DATES or cluster['p2'] not in DATES:
            print("warning: %s or %s not in persons sheet" % (cluster['p1'], cluster['p2']))
            continue
        check_dates_compatible(cluster['p1'], DATES[cluster['p1']], cluster['p2'], DATES[cluster['p2']], cluster['cltype'], cluster['textrefs'])

def main():
    clustersFromFile("../csv/DergeTengyur.csv")
    clustersFromFile("../csv/DergeKangyur.csv")
    datesFromFile("../csv/Persons-Ind.csv")
    datesFromFile("../csv/Persons-Tib.csv")
    check_clusters_coherence()

main()