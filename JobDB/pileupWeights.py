#!/usr/bin/env python

from src.messageLogger import messageLogger as log
from optparse import OptionParser
from src.weights import getWeight, getWeightString

import ROOT
import pickle


def getTreeFromFile(fileName, treePath):
    log.logDebug("Getting tree '%s'\n  from file %s" % (treePath, fileName))

    tree = ROOT.TChain(treePath)
    tree.Add(fileName)

    if (tree == None):
        log.logError("Could not get tree '%s'\n  from file %s" % (treePath, fileName))
        return None
    else:
        tree.SetDirectory(0)
        return tree


def main():
    log.logDebug("Creating vertex-weight dict")
    weightDict = {}
    nDataDict = {}
    nMCDict = {}

    pickleFile = "weights.pkl"
    cutStringRaw = "nVertices == %d"

    # data
    log.logDebug("Producing nVertex distribution for data")
    file = "/Volumes/Data/SUSY/Histos/sw428v0440/cutsV18SignalHighPt/sw428v0440.cutsV18SignalHighPt.Data_Run2011A.root"
    treePath = "cutsV18SignalHighPtFinalTrees/EEDileptonTree"

    treeData = getTreeFromFile(file, treePath)
    i = 1
    cutString = cutStringRaw % (i)
    nEventsTotal = float(treeData.GetEntries())
    nEvents = float(treeData.GetEntries(cutString))
    while (nEvents > 0):
        nDataDict['%d' % i] = nEvents / nEventsTotal
        i += 1
        cutString = cutStringRaw % (i)
        nEvents = int(treeData.GetEntries(cutString))

    # mc
    log.logDebug("Producing nVertex distribution for MC")
    file = "/Volumes/Data/SUSY/Histos/Scan/test.cutsV18GenJets.Scan_AOD.root"
    treePath = "cutsV18GenJetshadronicTree/Trees/MC"

    treeMC = getTreeFromFile(file, treePath)
    i = 1
    cutString = cutStringRaw % (i)
    nEventsTotal = float(treeMC.GetEntries())
    nEvents = float(treeMC.GetEntries(cutString))
    while (nEvents > 0):
        nMCDict['%d' % i] = nEvents / nEventsTotal
        i += 1
        cutString = cutStringRaw % (i)
        nEvents = int(treeMC.GetEntries(cutString))


    for i in range(1, 30):
        key = "%d" % i
        weight = 1.0
        if (nDataDict.has_key(key) and nMCDict.has_key(key)):
            weight = nDataDict[key] / nMCDict[key]
        weightDict['%d' % i] = weight

    log.logDebug("nDataDict: %s" % nDataDict)
    log.logDebug("nMCDict: %s" % nMCDict)
    log.logHighlighted("weightDict: %s" % weightDict)


    log.logInfo("Dumping weigths into %s" % pickleFile)
    pFile = open(pickleFile, 'wb')
    pickle.dump(weightDict, pFile)
    pFile.close()

    log.logInfo("Testing weights")
    for i in range(1, 30):
        log.logInfo("%d: %f" % (i, getWeight(i)))

    log.logInfo("WeightString: %s" % getWeightString())

    return


# entry point
if (__name__ == "__main__"):
    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                                  help="talk about everything")

    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    main()
