import csv

ROLEEVENTS = {
    "translator": "transation1",
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

def getFromFile(fname, res):
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
            if textid not in res['pertext']:
                res['pertext'][textid] = {}
            textinfo = res['pertext'][textid]
            if event not in textinfo:
                textinfo[event] = []
            else:
                for p in textinfo[event]:
                    if p not in res['perperson']:
                        res['perperson'][p] = set()
                    res['perperson'][p].add(personid)
                    if personid not in res['perperson']:
                        res['perperson'][personid] = set()
                    res['perperson'][personid].add(p)
            textinfo[event].append(personid)

def addToPersonFile(fnamesrc, fnamedst, res, seenpersons):
    with open(fnamesrc, newline='') as csvfile:
        rows = []
        reader = csv.reader(csvfile)
        for row in reader:
            pid = row[0]
            if pid in res['perperson']:
                workedwith = ','.join(list(res['perperson'][pid]))
                #print(workedwith)
                row.insert(10,workedwith)
            rows.append(row)
    with open(fnamedst, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_MINIMAL)
        for row in rows:
            writer.writerow(row)

def main():
    res = {'pertext': {}, 'perperson': {}}
    seenpersons = []
    getFromFile("../csv/DergeTengyur.csv", res)
    getFromFile("../csv/DergeKangyur.csv", res)
    addToPersonFile("../csv/Persons-Ind.csv", "../csv/Persons-Ind-ww.csv", res, seenpersons)
    addToPersonFile("../csv/Persons-Tib.csv", "../csv/Persons-Tib-ww.csv", res, seenpersons)

main()