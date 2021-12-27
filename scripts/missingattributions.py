import csv

RKTSTOD = {}
DTORKTS = {}
with open('../csv/derge-rkts.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        RKTSTOD[row[0]] = row[1]
        DTORKTS[row[1]] = row[0]

RKTSATTR = {}
with open('../csv/rkts-actors.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        d = RKTSTOD[row[0]]
        if d not in RKTSATTR:
            RKTSATTR[d] = {}
        if row[1] not in RKTSATTR[d]:
            RKTSATTR[d][row[1]] = []
        RKTSATTR[d][row[1]].append(row[2])

ATIIATTR = {}

with open('../csv/DergeKangyur.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        if row[3] == "" or ('?' in row[3]) or not row[3].startswith("P"):
            continue
        if row[0] not in RKTSATTR:
            continue
        if row[2] in RKTSATTR[row[0]]:
            del RKTSATTR[row[0]][row[2]]
            continue
        #if row[3] in RKTSATTR[row[0]][row[2]]:
        #    RKTSATTR[row[0]][row[2]].remove(row[3])
        #    continue
        #if row[0] not in ATIIATTR:
        #    ATIIATTR[row[0]] = {}
        #if row[1] not in ATIIATTR[row[0]]:
        #    ATIIATTR[row[0]][row[2]] = []
        #ATIIATTR[row[0]][row[2]].append(row[3])

with open('../csv/DergeTengyur.csv',  newline='') as csvfile:
    srcreader = csv.reader(csvfile, delimiter=',')
    for row in srcreader:
        if row[3] == "" or ('?' in row[3]) or not row[3].startswith("P"):
            continue
        if row[0] not in RKTSATTR:
            continue
        if row[2] in RKTSATTR[row[0]]:
            del RKTSATTR[row[0]][row[2]]
            continue

for d in RKTSATTR:
    dinfo = RKTSATTR[d]
    for r in dinfo:
        persons = dinfo[r]
        for p in persons:
            print("%s,%s,%s" % (d, r, p))