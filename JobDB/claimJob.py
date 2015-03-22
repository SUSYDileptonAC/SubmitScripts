#!/usr/bin/env python

from src.messageLogger import messageLogger as log
from src.job import Job
import time


def claimjob(config, dryRun=False, many=False, fast=False, keepTemp=False):
    if (not fast):
        sleepTime = 23
        log.logInfo("Sleeping for %d seconds" % sleepTime)
        time.sleep(sleepTime)

    log.logInfo("Connecting to JobDB")
    from src.jobDB import JobDB
    db = JobDB(config, "jobDB")

    nJobs = 1
    if (many):
        nJobs = 3

    log.logInfo("Claiming %d jobs" % nJobs)
    jobs = db.claimJob(dryRun=dryRun, nJobs=nJobs)
    for job in jobs:
        log.logInfo("Running job %s" % job.name)
        log.logInfo("Job parameters: m0 = %d, m12 = %d" % (job.m0, job.m12))
        job.makeDataCard()
        job.run(dryRun=dryRun, keepTemp=keepTemp)

    if (not dryRun):
        for job in jobs:
            log.logInfo("Updating next job")
            job.setParameter({"status": Job.Stati.done})
            db.updateJob(job)
            log.logInfo("Done.")

    log.logInfo("Finished.")
    return


def main():
    from optparse import OptionParser
    from src.helpers import BetterConfigParser

    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                                  help="talk about everything")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is jobDB.ini")
    parser.add_option("-n", "--dryRun", dest="dryRun", action="store_true", default=False,
                                  help="Don't do the calculation itself")
    parser.add_option("-m", "--many", dest="many", action="store_true", default=False,
                                  help="Run more than one job")
    parser.add_option("-f", "--fast", dest="fast", action="store_true", default=False,
                                  help="Don't sleep")
    parser.add_option("-t", "--temp", dest="temp", action="store_true", default=False,
                                  help="Don't remove temp directory")

    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    config = BetterConfigParser()
    if opts.Config == []:
        opts.Config = ["jobDB.ini"]
    config.read(opts.Config)

    claimjob(config, dryRun=opts.dryRun, many=opts.many, fast=opts.fast, keepTemp=opts.temp)


#entry point
if (__name__ == "__main__"):
    main()


