#! /usr/bin/env python
'''
Created on 26.07.2009

@author: heron
'''
import os.path
import sys
import re
import subprocess
import time
#for 2.6 this is better :(
import hashlib
#import md5
from optparse import OptionParser

import src.mainConfig

def md5Sum(filePath):
    chunkSize = 8096
    EOF = False
    file = open(filePath, "r")
    sum = hashlib.md5()
#    sum = md5.new()
    while not EOF:
        data = file.read(chunkSize)
        EOF = (data == "")
        if not EOF:
            sum.update(data)
    return sum.hexdigest()

def rootFileValid(path):
    from ROOT import TFile
    result = True
    file = TFile(path)
    result &= file.GetSize() > 0
    result &= not file.TestBit(TFile.kRecovered)
    result &= not file.IsZombie()
    if not result: print "WARNING: omitting damaged file '%s'"%path
    return result
    
    
def getMd5List(sources):
    result = []
    for filePath in sources:
        result.append((filePath, md5Sum(filePath),
                       time.asctime(time.localtime( os.path.getctime(filePath) ) )))
    return result

def readableIntList(numbers, minRow=2):
    result = []
    numbers = sorted(list(numbers))
    currentRow = [ int(numbers[0]) ]
    for i in numbers[1:]:
        i = int(i)
        if currentRow[-1] == i - 1:
            currentRow.append(i)
        else:
            if len(currentRow) > minRow:
                result.append("%s-%s" % (currentRow[0], currentRow[-1]))
            else:
                for single in currentRow:
                    result.append("%s" % single)
            currentRow = [i]
    if len(currentRow) > minRow:
        result.append("%s-%s" % (currentRow[0], currentRow[-1]))
    else:
        for single in currentRow:
            result.append("%s" % single)
    return ", ".join(result)

    
def histoListToString(list):
    result = []
    for flag in list:
        for task in list[ flag ]:
            firstTask = True
            for sample in list[ flag ][ task ]:
                padding = len(flag)
                readableList = readableIntList(list[ flag ][ task ][sample])
                if firstTask:
                    result.append("%s: %s: %s: %s" % (flag, task, sample, readableList))
                else:
                    nextLine = ""
                    for i in range(len(flag) + 2 + len(task) + 2):
                        nextLine += " "
                    nextLine += "%s: %s" % (sample, readableIntList(list[ flag ][ task ][sample]))
                    result.append(nextLine)
                firstTask = False
    return result

def getUnmergedHistos(filterTask=None, filterFlag=None, fileList=None):
    settings = src.mainConfig.MainConfig()
    if fileList == None:
        fileList = os.listdir(settings.localhistopath)


    #quick hack to remove EDM files from merging. Better: look into files and merge EDM files correctly.
    fileList = filter(lambda x: not ".EDM" in x, fileList)

    result = {}
                                 
                         
    #versionReStrings[2007008] = versionReStrings[2007007]
    #~ stringTemplate = "(.*)\.(.*)\.(.*)_([0-9]*)_([0-9]*)_(.*).root"
    stringTemplate = "(.*)\_(.*)\_(.*)_([0-9]*).root"
    fileNameRE = re.compile(stringTemplate)
    for fileName in fileList:
        groups = fileNameRE.search(fileName)
        if not groups == None:
            #~ (flag, task, sample, fileNumber) = groups.groups()[:4]
            fileNameParts = fileName.split("_")
            flag =  fileNameParts[0]
            task =  fileNameParts[1]
            fileNumber = fileNameParts[-1]
            fileNumber = fileNumber.replace(".root","")
            sample = ""
            del fileNameParts[0]
            del fileNameParts[0]
            del fileNameParts[-1]
            for fileNamePart in fileNameParts:
                if sample == "":
                    sample = "%s"%(fileNamePart)
                else:
                    sample = "%s_%s"%(sample,fileNamePart)
            retries = None
            if len(groups.groups()) == 5:
                retries = groups.groups()[4]
            elif len(groups.groups()) == 6:
                retries = groups.groups()[4]
            if flag == None or task == None or sample == None or fileNumber == None:
                raise StandardError, "could not parse '%s'. " % (fileName)
            if (filterTask == None or filterTask == task) and\
               (filterFlag == None or filterFlag == flag):
                if not flag in result:
                    result[flag] = {}
                if not task in result[flag]:
                    result[flag][task] = {}
                if not sample in result[flag][task]:
                    result[flag][task][sample] = set()
                result[flag][task][sample].add(int(fileNumber))
        
    return result

def __testTripple(toTest, done):
    inDone = False
    testPassed = None
    for tripple in done:
        if toTest[0] == tripple[0]:
            inDone=True
            testPassed = (toTest[1] == tripple[1])
    return (inDone, testPassed)

def removeDone( sources, destPathName, verbose=True):
    result = []
    if os.path.exists(destPathName) and os.path.exists(destPathName.replace(".root",".merged")):
        result.append(destPathName)
        logFile = open(destPathName.replace(".root",".merged"),"r")
        log = eval(logFile.read())
        md5List = getMd5List(sources)
        for oldTripple in log:
            inNewList = False
            for newTripple in md5List:
              inNewList = inNewList or oldTripple[0] == newTripple[0]
            if not inNewList:
                return sources
        for tripple in md5List:
            (inDone, testPassed) = __testTripple(tripple, log)
            if inDone:
                if not testPassed: 
                    if verbose: print "WARNING '%s' is corrupted. restarting merge from scratch!"%tripple[0]
                    return sources # if one test failed resart merge from scratch
               # else:
               #     print "skipping", tripple
            else:
                result.append(tripple[0])
    else:
        result = sources
    return result

def findLastRetry(path):
    from glob import glob
    paths = glob(path.replace(".root","_*.root"))
    #~ expr = re.compile(path.replace(".root","_([0-9]*)_(.*).root"))
    expr = re.compile(path.replace(".root","_([0-9]*).root"))
    return sorted(paths, key=lambda x: int(expr.search(x).groups()[0]))[-1]
        

def addHistos(unmergedList=None, dryRun=False, verbose=True, sampleFilter = None):
    from re import match
    result = ""
    settings = src.mainConfig.MainConfig()
    if unmergedList == None: 
        unmergedList = getUnmergedHistos(settings.task, settings.flag)
    for flag in unmergedList:
        
        for task in unmergedList[flag]:
            for sample in unmergedList[flag][task]:
                if (not sampleFilter == None) and  match(sampleFilter, sample) == None:
                    print "skipping",sample, sampleFilter
                    continue
                #~ rawSources = [ os.path.join(settings.localhistopath, "%s.%s.%s_%s.root" % (flag, task, sample, i)) for i in unmergedList[flag][task][sample] ]
                rawSources = [ os.path.join(settings.localhistopath, "%s_%s_%s_%s.root" % (flag, task, sample, i)) for i in unmergedList[flag][task][sample] ]
                sources = rawSources

                #~ for source in rawSources:
            #~ sources.append(findLastRetry(source))

                sources = filter(rootFileValid, sources)
                destDir = os.path.join(settings.mergedhistopath, flag, task)
                dest = os.path.join(destDir, "%s.%s.%s.root" % (flag, task, sample))
                argv = ["hadd", dest+"tmp.root"]
                argv.extend(removeDone(sources, os.path.join(destDir, "%s.%s.%s.root" % (flag, task, sample))))
                if verbose: print "merging %s %s %s" % (flag, task, sample)
                result += "%s\n" % argv
                if len(unmergedList[flag][task][sample]) == 1:
                    argv = ["cp", sources[0], dest]
                if not dryRun:
                    if not os.path.exists(destDir):
                        os.makedirs(destDir)
                    if len(sources) > 800:
                        sourceChunks=[sources[x:x+800] for x in xrange(0, len(sources), 800)]
                        num= len(sourceChunks)
                        for index, chunk in enumerate(sourceChunks):
                            dest = dest = os.path.join(destDir, "%s.%s.%s_%d.root" % (flag, task, sample,index))
                            argv = ["hadd",dest+"tmp.root"] 
                            argv.extend(removeDone(chunk, os.path.join(destDir, "%s.%s.%s_%d.root" % (flag, task, sample,index))))
                            
                            (stdout,stderr)=subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                            (stdout,stderr)=subprocess.Popen(["mv", dest+"tmp.root",dest], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                                    
                            logContent = "[%s]"%( ",\n".join([ "('%s', '%s', '%s')"% tripple for tripple in getMd5List(sources)]))
                            logFile = open(os.path.join(destDir, "%s.%s.%s_%d.merged" % (flag, task, sample,index)), "w")
                            logFile.write(logContent)
                            logFile.close()
                        dest = os.path.join(destDir, "%s.%s.%s.root" % (flag, task, sample))    
                        argv = ["hadd","-f",dest]
                        for i in range(0,num):
                            argv.append(os.path.join(destDir, "%s.%s.%s_%d.root" % (flag, task, sample,i)))  
                        (stdout,stderr)=subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()                                
                    else:
                        
                        (stdout,stderr)=subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                        (stdout,stderr)=subprocess.Popen(["mv", dest+"tmp.root",dest], stdout=subprocess.PIPE, stderr=subprocess.PIPE).communicate()
                                
                        logContent = "[%s]"%( ",\n".join([ "('%s', '%s', '%s')"% tripple for tripple in getMd5List(sources)]))
                        logFile = open(os.path.join(destDir, "%s.%s.%s.merged" % (flag, task, sample)), "w")
                        logFile.write(logContent)
                        logFile.close()

    if verbose:
        print "************* Summary ********************"
        print "\n".join(histoListToString(unmergedList))
    return result

def main(argv=None):
    if argv == None:
        argv = sys.argv[1:]
    parser = OptionParser()
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
    parser.add_option("-q", "--quiet", action="store_false", dest="verbose", default=True,
                          help="Verbose mode off.")
    parser.add_option("-n", "--dry-run", action="store_true", dest="dryrun", default=False,
                          help="Dry-run mode, no job submission.")
    parser.add_option("-t", "--task", dest="task", nargs=1, default=None,
                          help="filter histograms for TASK.")
    parser.add_option("-f", "--flag", dest="flag", nargs=1, default=None,
                          help="filter histograms for FLAG.")
    parser.add_option("-s", "--sample", dest="sample", nargs=1, default=None,
                          help="filter histograms for SAMPLE.")

    (opts, args) = parser.parse_args(argv)
    if opts.Config == []:
        opts.Config = [ "Input/default.ini" ]

    settings = src.mainConfig.MainConfig(opts.Config, opts)

    addHistos(verbose=opts.verbose, dryRun=opts.dryrun, sampleFilter=opts.sample)

if __name__ == '__main__':
    main()
