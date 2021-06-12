import csv

NAMESTOPERSONS = {}
PERSONSTONAMES = {}

def getFromFile(fname):
    with open(fname, newline='') as csvfile:
        reader = csv.reader(csvfile)
        # skip first two lines:
        next(reader)
        next(reader)
        for row in reader:
            textid = row[0]
            personid = row[3]
            personname = row[5]
            if personid == "" or '?' in personid or personname == "" or "," in personid:
                continue
            if personname not in NAMESTOPERSONS:
                NAMESTOPERSONS[personname] = {}
            if personid not in PERSONSTONAMES:
                PERSONSTONAMES[personid] = {}
            if personid not in NAMESTOPERSONS[personname]:
                NAMESTOPERSONS[personname][personid] = []
            NAMESTOPERSONS[personname][personid].append(textid)
            if personname not in PERSONSTONAMES[personid]:
                PERSONSTONAMES[personid][personname] = []
            PERSONSTONAMES[personid][personname].append(textid)

def main():
    getFromFile("../csv/DergeTengyur.csv")
    getFromFile("../csv/DergeKangyur.csv")
    for name, nameinfo in NAMESTOPERSONS.items():
        if len(nameinfo.keys()) > 1:
            print(name)
            for personid, textidlist in nameinfo.items():
                print("    "+personid+"  in  "+",".join(textidlist))
    # for name, nameinfo in PERSONSTONAMES.items():
    #     if len(nameinfo.keys()) > 1:
    #         print(name)
    #         for personid, textidlist in nameinfo.items():
    #             print("    "+personid+"  in  "+",".join(textidlist))

main()