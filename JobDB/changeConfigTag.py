#!/usr/bin/env python
'''
Created on 26.01.2012

@author: heron
'''
from src.messageLogger import messageLogger as log

from changeStatus import scanDefaults

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

    parser.add_option("-c", "--configTag", dest="configTag", action="store", default=None,
                          help="new configTag to use")

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

    log.logInfo("marking jobs in with configTag  '%s'" % (opts.configTag))

    db = JobDB(config, "jobDB")

    for scanName in opts.scans:
        section = Section(config, "scan:%s" % scanName, scanDefaults)
        newConfigTag = opts.configTag
        if opts.configTag == None:
            newConfigTag = section.configTag
            log.logInfo("no configTag given, reading '%s' from configfiles..." % newConfigTag)

        jobsToUpdate = {}
        jobSelection = {"scanName":scanName}
        numJobs = db.countJobs(**jobSelection)
        jobs = db.getJobs(**jobSelection)
        statusCounter = 0
        for job in jobs:
            job.setParameter({"configTag":newConfigTag})
            jobsToUpdate[job.name] = job
            log.logDebug("updating '%s' to status %s" % (job.name, job.status))
            statusCounter += 1
            log.statusBar(statusCounter, numJobs , message="scanning Jobs")

        log.logInfo("Found %i jobs to change." % len(jobsToUpdate))
        statusCounter = 0
        for job in jobsToUpdate.values():
            db.updateJob(job, force=True)
            log.statusBar(statusCounter, len(jobsToUpdate) , message="writing Jobs")
            statusCounter += 1

if __name__ == '__main__':
    main()
