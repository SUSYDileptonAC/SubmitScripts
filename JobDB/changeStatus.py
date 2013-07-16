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
                }

def main():
    from optparse import OptionParser
    from src.helpers import BetterConfigParser, Section, getDileptonTrees
    from src.jobDB import JobDB
    from src.job import Job

    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                                  help="talk about everything")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is jobDB.ini")

    parser.add_option("-s", "--scan", dest="scans", action="append", default=[],
                          help="names of scans to add from configuration file. Default is all found.")

    parser.add_option("-c", "--channel", dest="channels", action="append", default=[],
                          help="Channels to add to judge status change")

    parser.add_option("-r", "--region", dest="region", default="SR2",
                          help="signal region to judge status change")

    parser.add_option("-f", "--min", dest="min", default="0",
                          help="yields > x change status")

    parser.add_option("-t", "--max", dest="max", default="1e10",
                          help="yields < x change status")

    parser.add_option("--newStatus", dest="status", default="important",
                          help="status to change into")

    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    config = BetterConfigParser()
    if opts.Config == []:
        opts.Config = ["jobDB.ini"]
    config.read(opts.Config)


    if opts.scans == []:
        opts.scans = [i.split("scan:")[1] for i in config.sections() if "scan:" in i]

    if opts.channels == []:
        log.logInfo("no channels given! using EE EMu MuMu")

    opts.min = eval(opts.min)
    opts.max = eval(opts.max)

    assert opts.status in dir(Job.Stati), "unknown status '%s'" % opts.status

    log.logInfo("marking jobs in channels %s and region '%s' with %.1e < sum(rate) < %.1e as '%s'" % (opts.channels, opts.region, opts.min, opts.max, opts.status))

    db = JobDB(config, "jobDB")

    for scanName in opts.scans:
        section = Section(config, "scan:%s" % scanName, scanDefaults)

        jobsToUpdate = {}
        jobsToDelete = []
        jobStati = {}
        jobSelection = {"scanName":scanName}
        numJobs = db.countJobs(**jobSelection)
        jobs = db.getJobs(**jobSelection)
        statusCounter = 0
        for job in jobs:
            rate = sum([job.rates["%s %s" % (opts.region, i)] for i in opts.channels])
            if opts.min < rate and rate < opts.max and job.status == Job.Stati.created:
                job.setParameter({"status":Job.Stati.important})
                jobsToUpdate[job.name] = job
                log.logDebug("updating '%s' to status %s" % (job.name, job.status))
            statusCounter += 1
            log.statusBar(statusCounter, numJobs , message="scanning Jobs")

        log.logInfo("Found %i jobs to change." % len(jobsToUpdate))
        statusCounter = 0
        for job in jobsToDelete:
            db.deleteJob(job)
            log.statusBar(statusCounter, len(jobsToDelete) , message="deleting Jobs")
            statusCounter += 1
        statusCounter = 0
        for job in jobsToUpdate.values():
            db.updateJob(job, force=True)
            log.statusBar(statusCounter, len(jobsToUpdate) , message="writing Jobs")
            statusCounter += 1

if __name__ == '__main__':
    main()
