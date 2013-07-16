#!/usr/bin/env python
'''
Created on 26.01.2012

@author: heron
'''
from src.messageLogger import messageLogger as log

scanDefaults = {"name": "scanName",
                "configTag": "test",
                "taskName": "pfDileptonCuts",
                "producerName": "DiLeptonTrees",
                "canvasWidth": 800,
                "canvasHeight": 800,
                "xBinTitle": "m_{0}",
                "xBinName": "susScanM0",
                "xBinColumn": "m0",
                "xBinning": [ 140, 210, 3010 ],
                "yBinTitle": "m_{1/2}",
                "yBinName": "susScanM12",
                "yBinColumn": "m12",
                "yBinning": [ 46, 90, 1010 ],
                "constants": {"A0": 0., "tanBeta": 10, "sigMu": 1., "mGluino":-1. , "mSquark":-1.},
                "means": {"pdfUncert":"(cteq66Up - cteq66Down)/cteq66"},
                "fromReference":{},
                "signalRegions": ["SR3"],
                "channels":["EE", "EMu", "MuMu", "ETau", "MuTau", "TauTau"],
                "meanForChannels":["xSection"],
                "jecUncertainty":0.075,
                "xyBinsFromFile": True,
                "vertexWeight":"weight",
                "tauHtBranch":"ht2",
                "llHtBranch":"ht",
                "tauNJetsBranch":"nJets2",
                "llNJetsBranch":"nJets",
                "rInOut": 0.13,
                "kTau":0.1,
                "annotations":[ [0.2, 0.895, "CMS Preliminary"], [0.2, 0.845, "#sqrt{s} = 7 TeV. #scale[0.6]{#int}Ldt = 4.98 fb^{-1}"]],
                "limits": "{}",
}

def main():
    from optparse import OptionParser
    from src.helpers import BetterConfigParser, Section, getDileptonTrees
    from src.jobDB import JobDB

    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                                  help="talk about everything")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is jobDB.ini")

    parser.add_option("-s", "--scan", dest="scans", action="append", default=[],
                          help="names of scans to add from configuration file. Default is all found.")


    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    config = BetterConfigParser()
    if opts.Config == []:
        opts.Config = ["jobDB.ini"]
    config.read(opts.Config)

    db = JobDB(config, "jobDB")

    if opts.scans == []:
        opts.scans = [i.split("scan:")[1] for i in config.sections() if "scan:" in i]

    for scanName in opts.scans:
        section = Section(config, "scan:%s" % scanName, scanDefaults)

        log.logInfo("creating jobs for '%s' from '%s'" % (scanName, section.path))
        trees = getDileptonTrees(section.path, "%s%s" % (section.taskName, section.producerName),
                                 objectNames=section.channels)


        db.createJobs(section, trees)


if __name__ == '__main__':
    main()
