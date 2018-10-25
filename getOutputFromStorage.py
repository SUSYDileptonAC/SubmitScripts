#! /usr/bin/env python
'''
Created on 22.10.2018

@author: teroerde
'''
# do 'pip install --user tqdm' before running this
#
# New downloader with progress bar and dynamic waiting times, uses multiprocessing 
# instead of threading. 
#
import sys, os, subprocess, time
from multiprocessing import Pool
from tqdm import tqdm
from optparse import OptionParser

from src.mainConfig import MainConfig
import src.srmTools as srmTools
import src.crab as crab
from run import getJobsFromGroups



def main():
    # create option parser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose mode.")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=["Input/default.ini"],
                      help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
    parser.add_option("-S", "--Source", dest="Source", action="append", default=None,
                      help="overwrite the source folder to start copying from.")
    parser.add_option("-w", "--wait", dest="wait", action="store_true", default=False,
                      help="Keep looping")
    parser.add_option("-p", "--processes", dest="processes", action="store", default=3, type="int",
                      help="Number of parallel processes to download")
    
    argv = sys.argv[1:]
    (opts, args) = parser.parse_args(argv)

    verbose = opts.verbose

    # set up MainConfig singelton
    settings = MainConfig(opts.Config)

    theStoragePath = settings.histogramoutputpath
    theLocalHistPath = settings.localhistopath
    theLocalLogPath = settings.analogpath
    
    baseWaitTime = 60 # base time to wait after each iteration
    incrementWaitTime = 120 # time to add to wait time every time no file is found; reset if a file is found again
    
    if (not os.path.exists(theLocalHistPath)):
        os.makedirs(theLocalHistPath)
    if (not os.path.exists(theLocalLogPath)):
        os.makedirs(theLocalLogPath)
    
    foundNothing = 0
    while True:
    
        pathList = []
        if opts.Source == None:
            print "Getting directory content of " + theStoragePath
            pathList.extend(srmTools.getDir(theStoragePath, verbose))
        else:
            for source in opts.Source:
                print "Getting directory content of " + source
                pathList.extend(srmTools.getDir(source, verbose))
        
        if len(pathList) == 0:
            # increase waiting time for next iteration
            foundNothing += 1
        else:
            # reset waiting time so output can quickly be fetched if there is anything left after this
            foundNothing = 0
        
        if not foundNothing:
            argTuples = []
            for fileName in pathList:
                if (os.path.splitext(fileName)[1] == ".log" or os.path.splitext(fileName)[1] == ".gz"):
                    name = nextFile.split("/")[-1]
                    localFilePath = theLocalLogPath + '/' +name+"_"+ os.path.basename(fileName)
                else:
                    localFilePath = theLocalHistPath + '/' + os.path.basename(fileName)

                argTuples.append( (fileName, localFilePath, verbose) )
        
            pool = Pool(processes=opts.processes)
            for _ in tqdm(pool.imap_unordered(copyFile, argTuples), total=len(argTuples), unit="file"):
                pass
            pool.close()
            pool.join()
            
        if not opts.wait:
            break
            
        waitTime = baseWaitTime + foundNothing * incrementWaitTime
        time_remaining = waitTime
        while time_remaining > 0:
            minutes_remaining = int(time_remaining / 60)
            seconds_remaining = time_remaining - minutes_remaining*60
            
            if minutes_remaining > 10:
                sleep_interval = 30
            else:
                sleep_interval = 1
            
            minutes_remaining = str(minutes_remaining).zfill(2)
            seconds_remaining = str(seconds_remaining).zfill(2)
            
            print "Sleeping for {}:{}, press [CTRL+C] to stop".format(minutes_remaining, seconds_remaining)
            
            
            time.sleep(sleep_interval)
            time_remaining -= sleep_interval
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[K")
        print("")
        sys.stdout.write("\033[F")
        sys.stdout.write("\033[K")

def copyFile(inputTuple):
    source, target, verbose = inputTuple
    
    rc = srmTools.copyFile(source, target, verbose)
    if (os.path.exists(target) == True) and rc == 0:
        srmTools.removeFile(source, verbose)
    else:
        print "ERROR: Copying failed: " + source          


# start main script
if __name__ == '__main__':
    main()


