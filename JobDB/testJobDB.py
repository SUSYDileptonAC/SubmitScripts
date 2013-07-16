#!/usr/bin/env python

'''
Created on 20.01.2012

@author: epsilon
'''


import os
import sqlobject
from src.job import Job, SQLJob
from src.messageLogger import messageLogger as log

def createDBConnection():
    dbFilename = os.path.abspath('test.db')
    if os.path.exists(dbFilename):
        os.unlink(dbFilename)
    connectionString = "sqlite:%s?timeout=5000" % (dbFilename)
    log.logInfo("Setting up DB connection: %s" % connectionString)
    connection = sqlobject.connectionForURI(connectionString)
    sqlobject.sqlhub.processConnection = connection
    return connection

def createTestJob():
    return Job()

def testJob():
    log.logInfo("Creating job table")

    SQLJob.createTable()

    testJob = createTestJob()
    parameters = {
                  'name': "Test",
                  'version': "Testv1.0",
                  'configTag': "combineTest",
                  }
    testJob.setParameter(parameters)
    parameters = testJob.getParameter()
    log.logDebug("Parameters: %s" % parameters)

    # Convert into SQLJob
    sqlJob = SQLJob()
    sqlJob.update(testJob)
    log.logDebug("SQLJob: %s" % sqlJob)
    sqlJob.name = "Brot"

    # convert back
    testJob2 = Job(sqlJob)
    parameters = testJob2.getParameter()
    log.logDebug("Parameters: %s" % parameters)

    testJob2.makeDataCard()
    #testJob2.run()

def testJobDB(config, dryRun=False):
    from src.jobDB import JobDB
    db = JobDB(config, "jobDB")
    newJob = Job()
    newJob.setParameter({"name": "lecker",
                  "version": "Testv1.1",
                  'configTag': "combineTest",
                  'xSection': 5.0,
                  'signalRegion': ["HighHT"], #, "HighMET", "HighHTMET"],
                  "yields": {'HighHT EE': 20, 'HighMET EE': 2, 'HighHTMET EE': 3,
                             'HighHT EMu': 9, 'HighMET EMu': 5, 'HighHTMET EMu': 6,
                             'HighHT MuMu': 15, 'HighMET MuMu': 8, 'HighHTMET MuMu': 9,
                             'HighHT ETau': 2, 'HighMET ETau': 2, 'HighHTMET ETau': 3,
                             'HighHT MuTau': 3, 'HighMET MuTau': 5, 'HighHTMET MuTau': 6,
                             'HighHT TauTau': 1, 'HighMET TauTau': 8, 'HighHTMET TauTau': 9,
                        }
                  })
    db.updateJob(newJob)

    for i in db.getJobs(version="Testv1.1"):
        log.logDebug("Job Content: %s" % i)
        i.makeDataCard()
        i.run(dryRun=dryRun)
        log.logDebug("Job Content: %s" % i)

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

    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    config = BetterConfigParser()
    if opts.Config == []:
        opts.Config = ["jobDB.ini"]
    config.read(opts.Config)

    createDBConnection()
    testJob()

    testJobDB(config, dryRun=opts.dryRun)

# entry point
if (__name__ == "__main__"):
    main()





