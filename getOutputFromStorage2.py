#! /usr/bin/env python

import sys, os, subprocess, Queue, threading, time
from optparse import OptionParser

from src.mainConfig import MainConfig
import src.srmTools as srmTools
import src.crab as crab
from run import getJobsFromGroups

# TODO:
#  * Load MainConfig -> DS, 24.07.2009: done
#  * Option parser for verbose mode -> DS, 24.07.2009: done
#  - Support more than 999 entries
#  * Extra thread for status bar -> DS, 24.07.2009: done
#  - print out received warnings
#  * hAdd downloaded files -> ME 27.07.2009: done


def main():
    # create option parser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose mode.")
    parser.add_option("-d", "--statusdelay", dest="statusdelay", nargs=1, default=10,
                      help="Delay between status info messages in seconds ('0' hides status messages).")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=["Input/default.ini"],
                      help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
    parser.add_option("-S", "--Source", dest="Source", action="append", default=None,
                      help="overwrite the source folder to start copying from.")
    parser.add_option("-s", "--skims", action="store_true", dest="skim", default=False,
                      help="Copy output of skim to localdatapath defined in.")
    parser.add_option("-f", "--flag", dest="flag", nargs=1, default='test',
                                        help="Set naming of the job to FLAG.")
    parser.add_option("-G", "--Groups", dest="Groups",
                                   help="Groups of jobs to run from the master list. If neither of 'not' 'and' 'or' are present or is taken. Else boolean logic is observed")

    argv = sys.argv[1:]
    (opts, args) = parser.parse_args(argv)

    # global paths
    global verbose
    global theStoragePath
    global theLocalHistPath
    global theLocalLogPath
    verbose = opts.verbose

    # set up MainConfig singelton
    settings = MainConfig(opts.Config)

    if opts.skim:
        print 'Skim copy'
        theJobs, theNonJobs = getJobsFromGroups(opts.Groups, False)
        theFlag = opts.flag
        theHash = crab.getHash(settings.skimcfgname)
        for theJob in theJobs:
            if settings.skimFromLocalDBS:
                primData = settings.masterConfig.get(theJob, 'localdbspath').split('/')[1]
            else:
                primData = settings.masterConfig.get(theJob, 'datasetpath').split('/')[1]
            theStoragePath = os.path.join(settings.storagepath, primData, theJob + '_' + theFlag, theHash)
            theLocalHistPath = os.path.join(settings.localdatapath, theFlag, theJob + '_' + theFlag)
            theLocalLogPath = settings.analogpath
            print 'From ' + theStoragePath
            print 'to ' + theLocalHistPath
            if not os.path.exists(theLocalHistPath):
                os.makedirs(theLocalHistPath)
            doCopy(opts)
    else:
        theStoragePath = settings.histogramstoragepath
        theLocalHistPath = settings.localhistopath
        theLocalLogPath = settings.analogpath
        doCopy(opts)

def doCopy(opts):
    # check for existence of paths
    if (not os.path.exists(theLocalHistPath)):
        os.makedirs(theLocalHistPath)
    if (not os.path.exists(theLocalLogPath)):
        os.makedirs(theLocalLogPath)
    # for multi-threaded output fetching
    global theThreadId
    theThreadId = 1
    global theListDirectories
    global theListFiles
    theListDirectories = Queue.Queue(0)
    theListDirectories.put(theStoragePath)
    theListFiles = Queue.Queue(0)

    # init file name replacing map
    replaceFilenameMap = {
        "download_1": 1
        }

    # get directory content and fill file queue
    pathList = []
    if opts.Source == None:
        print "Getting directory content of " + theStoragePath
        pathList.extend(srmTools.getDir(theStoragePath, verbose))
    else:
        for source in opts.Source:
            print "Getting directory content of " + source
            pathList.extend(srmTools.getDir(source, verbose))
    for subPath in pathList:
    #srmTools.getDir(theStoragePath, verbose):
        if (subPath[len(subPath) - 1] != '/'):
            # ignore directories
            theListFiles.put(os.path.normpath(subPath))

    # start status thread
    if (opts.statusdelay != 0):
        StatusInfoThread(theListFiles.qsize(), float(opts.statusdelay), verbose).start()

    # start threads to copy all found files
    for iThread in range(0, 6):
        FetchingThread(verbose, replaceFilenameMap).start()
        # do not start all threads at the same time
        time.sleep(5)


# Thread class for file fetching
class FetchingThread(threading.Thread):
    def __init__(self, verbose=False, replaceFilenameMap={}):
        self.verbose = verbose
        self.replaceFilenameMap = replaceFilenameMap
        threading.Thread.__init__(self)

    def run(self):
        global theThreadId
        self.threadId = theThreadId
        theThreadId += 1
        if (self.verbose): print "(thread " + str(self.threadId) + "): Thread started"

        nErrors = 0
        #rejectString = ""

        while (theListFiles.empty() == False):
            nextFile = theListFiles.get()
            if (self.verbose):
                print "(thread " + str(self.threadId) + "): Getting file " + os.path.basename(nextFile)

            # sort out log files
            if (os.path.splitext(nextFile)[1] == ".log"):
                localFilePath = theLocalLogPath + '/' + os.path.basename(nextFile)
            else:
                localFilePath = theLocalHistPath + '/' + os.path.basename(nextFile)

            #change file name if it is in self.replaceFilenameMap
            srmFileName = os.path.splitext(os.path.split(nextFile)[1])[0]
            if srmFileName in self.replaceFilenameMap:
                dirNumber = self.replaceFilenameMap[ srmFileName ]
                localFileName = nextFile.split(theStoragePath)[1].split(os.path.sep)[ dirNumber ]
                localFileName += os.path.splitext(nextFile)[1]
                if (self.verbose): print " renaming %s to %s" % (nextFile, localFileName)
                localFilePath = os.path.join(os.path.split(localFilePath)[0], localFileName)

            try:
                srmTools.copyFile(nextFile, localFilePath, self.verbose)
                if (os.path.exists(localFilePath) == True):
                    srmTools.removeFile(nextFile, self.verbose)
                else:
                    print "ERROR: Copying failed: " + nextFile
                    nErrors += 1
            except KeyboardInterrupt:
                print "Copying aborted: %s" % nextFile

        if (nErrors != 0):
            print "(thread " + str(self.threadId) + "): There were " + str(nErrors) + " copying errors!"
        if (self.verbose): print "(thread " + str(self.threadId) + "): Thread finished"


# Thread class for status information
class StatusInfoThread(threading.Thread):
    def __init__(self, nTotalFiles, delay=10, verbose=False):
        self.nTotalFiles = nTotalFiles
        self.delay = delay
        self.verbose = verbose
        threading.Thread.__init__(self)

    def run(self):
        import sys
        self.threadId = "Status"
        if (self.verbose): print "(thread " + str(self.threadId) + "): Thread started"

        while (theListFiles.empty() == False):
            nFilesLeft = theListFiles.qsize()
            percentage = 100 * (self.nTotalFiles - nFilesLeft) / self.nTotalFiles
            sys.stdout.write("\r\033[1;34mStatus: %i%% (%i files left)\033[m" % (percentage, nFilesLeft))
            sys.stdout.flush()
            time.sleep(self.delay)

        if (self.verbose): print "(thread " + str(self.threadId) + "): Thread finished"

# start main script
if __name__ == '__main__':
    main()


