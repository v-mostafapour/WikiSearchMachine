#!/usr/bin/python
#coding: utf8

# Author: Sai Teja Jammalamadaka
# PGSSP Student : IIIT-Hyderabad
# Roll: 201350905
# Written for the Spring Semester 2015 IRE Course

import QueryHandler
import sys
from sys import argv
import operator
import Indexer
import bisect
import bz2
import time
import TokenStemmer

script, infile = argv

TotalDocNum = 0
docIDTitleMap = {}
def getdocIDTitleMap():
    global TotalDocNum
    with open(infile+".titles","r") as titles_file:
        for line in titles_file:
            parts = line.strip().split('=')
            if len(parts) == 2:
                id = parts[0]
                title = parts[1]
                docIDTitleMap[id] = title
    #print "count of docs = {0}".format(len(docIDTitleMap))
    TotalDocNum = len(docIDTitleMap)
    #print "TotalDocNum = {0}".format(TotalDocNum)

indexFileCount = 0
indexFileWordMap = {}
sortedIndexFileWordMapKeys = []
def getIndexFileWordMap():
    global indexFileCount, indexFileWordMap, sortedIndexFileWordMapKeys
    with open(infile+".indexWordMap","r") as temp_file:
        for line in temp_file:
            parts = line.strip().split('=')
            if len(parts) == 2:
                index = parts[1]
                word = parts[0]
                indexFileWordMap[index] = word
    indexFileCount = len(indexFileWordMap)
    sortedIndexFileWordMapKeys = sorted(indexFileWordMap.keys())

indexFileTitleCount = 0
indexFileTitleMap = {}
sortedIndexFileTitleMapKeys = []
def getIndexFileTitleMap():
    global indexFileTitleCount, indexFileTitleMap, sortedIndexFileTitleMapKeys, TotalDocNum
    with open(infile+".titlesCount","r") as temp_file:
        TotalDocNum = int(temp_file.readline())
    with open(infile+".indexTitleMap","r") as temp_file:
        for line in temp_file:
            parts = line.strip().split('=')
            if len(parts) == 2:
                docID = int(parts[1])
                index = parts[0]
                indexFileTitleMap[docID] = index
    indexFileTitleCount = len(indexFileTitleMap)
    sortedIndexFileTitleMapKeys = sorted(indexFileTitleMap.keys())

# This method checks for the word in the index part files and returns a frequency object
def checkInIndexFileWordMap(term):
    pos = bisect.bisect(sortedIndexFileWordMapKeys,term)
    if pos > 0:
        pos = pos - 1
    key = sortedIndexFileWordMapKeys[pos]
    index = indexFileWordMap[key]
    #print "key = {0} and index = {1}".format(key,index)
    with bz2.BZ2File("{0}.index{1}.bz2".format(infile,index), 'rb', compresslevel=9) as ipartF:
        #print "checking file {0}.index{1}.bz2".format(infile,index)
        for line in ipartF:
            if line.startswith("{0}=".format(term)):
                parts = line.strip().split("=")
                if len(parts) == 2:
                    #word = parts[0]
                    ffo = Indexer.getFOFromLine(parts[1])
                    return ffo
    return {}
    
# This method checks for the docID in the title part files and returns the title
def checkInIndexFileTitleMap(docID):
    pos = bisect.bisect(sortedIndexFileTitleMapKeys,int(docID))
    if pos > 0:
        pos = pos - 1
    key = sortedIndexFileTitleMapKeys[pos]
    index = indexFileTitleMap[key]
    #print "indexFileTitleMap::: key = {0} and index = {1}".format(key,index)
    with bz2.BZ2File("{0}.titles{1}.bz2".format(infile,index), 'rb', compresslevel=9) as ipartF:
        #print "checking file {0}.index{1}.bz2".format(infile,index)
        for line in ipartF:
            if line.startswith("{0}=".format(docID)):
                parts = line.strip().split("=")
                if len(parts) == 2:
                    #return "{0}\t\t=\t{1}".format(docID,parts[1])
                    return parts[1]
    #return "{0}".format(docID)
    return ""

def intersectLists(lists):
    if len(lists)==0:
        return []
    #start intersecting from the smaller list
    lists.sort(key=len)
    #print lists
    new_lists = []
    for l in lists:
        if len(l) != 0:
            new_lists.append(l)
    #print new_lists
    if len(new_lists)==0:
        return []
    return list(reduce(lambda x,y: set(x)&set(y),new_lists))

def getSortedTuples(freq_map):
    sorted_tuples = sorted(freq_map.iteritems(), key=operator.itemgetter(1))
    return sorted_tuples
    
def doSearch(queryObject, numOfResults):
    queryDocList = []
    ffoMap = {}
    gTqueryDocList = {}
    tTqueryDocList = {}
    bTqueryDocList = {}
    cTqueryDocList = {}
    iTqueryDocList = {}
    
    for gT in queryObject["gT"]:
        ffoMap[gT] = checkInIndexFileWordMap(gT)
    for tT in queryObject["tT"]:
        ffoMap[tT] = checkInIndexFileWordMap(tT)
    for bT in queryObject["bT"]:
        ffoMap[bT] = checkInIndexFileWordMap(bT)
    for cT in queryObject["cT"]:
        ffoMap[cT] = checkInIndexFileWordMap(cT)
    for iT in queryObject["iT"]:
        ffoMap[iT] = checkInIndexFileWordMap(iT)
    
    toUseDocIdList = set([])
    if queryObject["type"] == "intersection":
        toIntersect = []
        for word in ffoMap:
            wordDocs = []
            for docid in ffoMap[word]:
                wordDocs.append(docid)
            toIntersect.append(set(wordDocs))
        #intersected = set(intersectLists(toIntersect))
        toUseDocIdList = set.intersection(*toIntersect)
    else:
        toUseAllDocIdList = []
        for word in ffoMap:
            toUseAllDocIdList.extend(ffoMap[word].keys())
        toUseDocIdList = set(toUseAllDocIdList)
                
    for gT in queryObject["gT"]:
        ffo = ffoMap[gT]
        if len(ffo) > 0:
            #ffoMap[gT] = ffo
            DF = len(ffo.keys())
            IDF = TotalDocNum / DF
            for docID in ffo.keys():
                if docID not in toUseDocIdList:
                    continue
#                 TF = ffo[docID]["t"] + ffo[docID]["b"] + ffo[docID]["c"] + ffo[docID]["i"]
#                 gTqueryDocList[docID] = TF * IDF
                if ffo[docID]["t"] > 0:
                    TF = ffo[docID]["t"]
                    tTqueryDocList[docID] = TF * IDF
                if ffo[docID]["b"] > 0:
                    TF = ffo[docID]["b"]
                    bTqueryDocList[docID] = TF * IDF
                if ffo[docID]["c"] > 0:
                    TF = ffo[docID]["c"]
                    cTqueryDocList[docID] = TF * IDF
                if ffo[docID]["i"] > 0:
                    TF = ffo[docID]["i"]
                    iTqueryDocList[docID] = TF * IDF
                
    for tT in queryObject["tT"]:
        ffo = ffoMap[tT]
        #print "tT = {0}, ffo = {1}".format(tT,ffo)
        if len(ffo) > 0:
            #ffoMap[tT] = ffo
            DF = len(ffo.keys())
            IDF = TotalDocNum / DF
            for docID in ffo.keys():
                if docID not in toUseDocIdList:
                    continue
                if ffo[docID]["t"] > 0:
                    TF = ffo[docID]["t"]
                    tTqueryDocList[docID] = TF * IDF
        #print "tTqueryDocList = {0}".format(tTqueryDocList)
    
    for bT in queryObject["bT"]:
        ffo = ffoMap[bT]
        #print "bT = {0}, ffo = {1}".format(bT,ffo)
        if len(ffo) > 0:
            #ffoMap[bT] = ffo
            DF = len(ffo.keys())
            IDF = TotalDocNum / DF
            #print "DF = {0} IDF = {1} TotalDocNum = {2}".format(DF,IDF,TotalDocNum)
            for docID in ffo.keys():
                if docID not in toUseDocIdList:
                    continue
                if ffo[docID]["b"] > 0:
                    TF = ffo[docID]["b"]
                    bTqueryDocList[docID] = TF * IDF
        #print "bTqueryDocList = {0}".format(bTqueryDocList)
    
    for cT in queryObject["cT"]:
        ffo = ffoMap[cT]
        if len(ffo) > 0:
            #ffoMap[cT] = ffo
            DF = len(ffo.keys())
            IDF = TotalDocNum / DF
            for docID in ffo.keys():
                if docID not in toUseDocIdList:
                    continue
                if ffo[docID]["c"] > 0:
                    TF = ffo[docID]["c"]
                    cTqueryDocList[docID] = TF * IDF
    
    for iT in queryObject["iT"]:
        ffo = ffoMap[iT]
        if len(ffo) > 0:
            #ffoMap[iT] = ffo
            DF = len(ffo.keys())
            IDF = TotalDocNum / DF
            for docID in ffo.keys():
                if docID not in toUseDocIdList:
                    continue
                if ffo[docID]["i"] > 0:
                    TF = ffo[docID]["i"]
                    iTqueryDocList[docID] = TF * IDF
    
    tfidfDOCMap = {}
    
#     if queryObject["type"] == "intersection":
#         #print "Doing Intersection Query"
#         #queryDocList = list(set(iTqueryDocList.keys()) & set(cTqueryDocList.keys()) & set(bTqueryDocList.keys()) & set(tTqueryDocList.keys()) & set(gTqueryDocList.keys()))
#         toIntersect = [iTqueryDocList.keys(),cTqueryDocList.keys(),bTqueryDocList.keys(),tTqueryDocList.keys(),gTqueryDocList.keys()]
#         queryDocList = intersectLists(toIntersect)
#         
#     else:
#         #print "Doing Regular Query"
#         queryDocList.extend(gTqueryDocList.keys())
#         queryDocList.extend(iTqueryDocList.keys())
#         queryDocList.extend(cTqueryDocList.keys())
#         queryDocList.extend(bTqueryDocList.keys())
#         queryDocList.extend(tTqueryDocList.keys())
        
    for doc in toUseDocIdList:
        #print doc
        TFIDF = 0
        if doc in iTqueryDocList:
            TFIDF += iTqueryDocList[doc]*0.2
        if doc in cTqueryDocList:
            TFIDF += cTqueryDocList[doc]*0.2
        if doc in bTqueryDocList:
            TFIDF += bTqueryDocList[doc]*0.1
        if doc in tTqueryDocList:
            TFIDF += tTqueryDocList[doc]*6
        if doc in gTqueryDocList:
            TFIDF += gTqueryDocList[doc]*0.2
        if TFIDF >0:
            tfidfDOCMap[doc] = TFIDF
    
    sorted_tuples = getSortedTuples(tfidfDOCMap)
    #print sorted_tuples
    sorted_tuples.reverse()
    #print sorted_tuples
    toReturnList = []
    topNtuples = sorted_tuples[:numOfResults]
    #topNtuples = sorted_tuples
    for pair in topNtuples:
        #print pair
        toReturnList.append(pair[0])
    #print toReturnList
    return toReturnList
    # return []

def getTitlesFromDocIds(docIDList):
    titlesList = []
    for docID in docIDList:
        titlesList.append(checkInIndexFileTitleMap(docID))
    return titlesList
def checkQueryInTitle(query,docTitleList):
    toReturn = [""]
    queryTokens = set(TokenStemmer.getStemmedTokens(query))
    for title in docTitleList:
        #print title
        if queryTokens == set(TokenStemmer.getStemmedTokens(title)):
            toReturn[0] = title
        else:
            toReturn.append(title)
    if toReturn[0] == "":
        del toReturn[0]
    return toReturn
    

start = int(round(time.time()*1000))

#getIndexPositionMap()
getIndexFileWordMap()
getIndexFileTitleMap()
#getdocIDTitleMap()  ## This consumes too much memory...



f = sys.stdin
queries =  []
for line in f.readlines():
    queries.append(line.strip())
queryNo = int(queries[0])
queries = queries[1:]

for query in queries:
    queryObject = QueryHandler.parseQuery(query)
    listOfDocIDs = doSearch(queryObject,10)
    print "Query = {0}".format(query)
    listOfTitles = getTitlesFromDocIds(listOfDocIDs)
    #if query is an article title, then make it first result...
    listOfTitles = checkQueryInTitle(query, listOfTitles)
    for title in listOfTitles:
        print title
    print ""
    
end = int(round(time.time()*1000))
with open(infile+".doneSearch","w") as done_file:
    toPrint = "Process is complete. Time Taken in milliseconds = {0}".format((end-start))
    print toPrint
    done_file.write(toPrint)