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
    from src.job import SQLJob

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
        availableScans = db.getDistinct("scanName")
        opts.scans = filter(lambda x: x in availableScans, opts.scans)

    for scanName in opts.scans:
        print "=== %s ==" % scanName
        print "   configTag:"
        for configTag in db.getDistinct("configTag", {"scanName":scanName}):
            print "      '%s' x %i" % (configTag, db.countJobs(scanName=scanName, configTag=configTag))
        print "   version:"
        for version in db.getDistinct("version", {"scanName":scanName}):
            print "      '%s' x %i" % (version, db.countJobs(scanName=scanName, version=version))
        print "   status:"
        for status in db.getDistinct("status", {"scanName":scanName}):
            print "      '%s' x %i" % (status, db.countJobs(scanName=scanName, status=status))


if __name__ == '__main__':
    main()
