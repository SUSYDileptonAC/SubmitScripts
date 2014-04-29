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
    stringTemplate = "(.*)\.(.*)\.(.*)_([0-9]*)_([0-9]*)_(.*).root"
    fileNameRE = re.compile(stringTemplate)
    for fileName in fileList:
        groups = fileNameRE.search(fileName)
        if not groups == None:
            (flag, task, sample, fileNumber) = groups.groups()[:4]
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
    expr = re.compile(path.replace(".root","_([0-9]*)_(.*).root"))
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
                rawSources = [ os.path.join(settings.localhistopath, "%s.%s.%s_%s.root" % (flag, task, sample, i)) for i in unmergedList[flag][task][sample] ]
                sources = []

                for source in rawSources:
			sources.append(findLastRetry(source))

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
				argv = ["hadd",dest]
				print argv
				for i in range(0,num):
					argv.append(os.path.join(destDir, "%s.%s.%s_%d.root" % (flag, task, sample,i)))  
				print argv
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

import unittest
class MergeHistosTest(unittest.TestCase):

    def setUp(self):
        self.originPath = os.path.abspath(os.path.curdir)
        src.mainConfig.MainConfig([ "Input/default.ini" ], None)

    def tearDown(self):
        src.mainConfig.MainConfig().tearDown()
        os.chdir(self.originPath)

    def testGetMd5List(self):
        result = getMd5List(["unittest/reference/flag.task.job_1.root", "unittest/reference/flag.task.job_2.root"])
        print result

    def testAddHistos(self):
        result = addHistos(self.compareList, True, False)
        for command in haddCommands:
            self.assertTrue(command in result)

    def testReadableIntList(self):
        testList = [1, 2, 3, 4, 5, 10, 12, 13, 14, 20 ]
        compare = "1-5, 10, 12-14, 20"
        result = readableIntList(testList, 2)
        self.assertEquals(result, compare)

    def testGetUnmergedHistos(self):
        result = getUnmergedHistos(None, None, self.testFileList)
        self.assertEquals(result, self.compareList)
        looseCutsOnly = {'CERNdefault': {'looseCuts': {'EMenrichedQCDpt30_80_Cern': [11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 26, 28, 29, 2, 30, 31, 32, 33, 34, 35, 37, 38, 39, 3, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 4, 50, 51, 52, 6, 7, 8, 9], 'WJets_madgraph_Cern': [12, 2], 'QCD100to250_madgraph_Cern': [10, 13, 14, 4, 5], 'EMenrichedQCDpt20_30_Cern': [11, 12, 13, 14, 18, 20, 21, 22, 23, 24, 26, 27, 3]}}}
        result = getUnmergedHistos("looseCuts", None, self.testFileList)
        self.assertEquals(result, looseCutsOnly)

    def testHistoListToString(self):
        result = histoListToString(getUnmergedHistos(self.testFileList))


    testFileList = [
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_10.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_11.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_12.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_13.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_14.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_15.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_16.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_17.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_18.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_19.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_1.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_20.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_21.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_22.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_23.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_24.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_25.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_26.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_27.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_28.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_29.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_2.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_3.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_4.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_6.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_8.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_9.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_11.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_12.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_13.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_14.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_15.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_16.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_17.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_18.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_19.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_21.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_23.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_24.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_25.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_26.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_28.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_29.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_2.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_30.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_31.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_32.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_33.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_34.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_35.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_37.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_38.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_39.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_3.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_40.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_41.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_42.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_43.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_44.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_45.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_46.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_47.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_48.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_49.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_4.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_50.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_51.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_52.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_6.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_7.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_8.root",
    "CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_9.root",
    "CERNdefault.leptonCuts.QCD1000toInf_madgraph_Cern_1.root",
    "CERNdefault.leptonCuts.QCD1000toInf_madgraph_Cern_2.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_10.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_13.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_14.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_16.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_17.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_2.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_3.root",
    "CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_7.root",
    "CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_1.root",
    "CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_3.root",
    "CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_6.root",
    "CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_7.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_1.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_2.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_3.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_4.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_5.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_6.root",
    "CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_7.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_10.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_11.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_2.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_5.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_6.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_8.root",
    "CERNdefault.leptonCuts.QCDpt15_Cern_9.root",
    "CERNdefault.leptonCuts.QCDpt170_Cern_3.root",
    "CERNdefault.leptonCuts.QCDpt170_Cern_4.root",
    "CERNdefault.leptonCuts.QCDpt170_Cern_6.root",
    "CERNdefault.leptonCuts.QCDpt300_Cern_2.root",
    "CERNdefault.leptonCuts.QCDpt300_Cern_3.root",
    "CERNdefault.leptonCuts.QCDpt30_Cern_2.root",
    "CERNdefault.leptonCuts.QCDpt30_Cern_3.root",
    "CERNdefault.leptonCuts.QCDpt30_Cern_5.root",
    "CERNdefault.leptonCuts.QCDpt470_Cern_1.root",
    "CERNdefault.leptonCuts.QCDpt470_Cern_2.root",
    "CERNdefault.leptonCuts.QCDpt470_Cern_3.root",
    "CERNdefault.leptonCuts.QCDpt470_Cern_4.root",
    "CERNdefault.leptonCuts.QCDpt800_Cern_1.root",
    "CERNdefault.leptonCuts.QCDpt800_Cern_3.root",
    "CERNdefault.leptonCuts.SUSY_LM0_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM10_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM11_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM1_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM2_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM3_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM4_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM5_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM6_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM7_Cern_1.root",
    "CERNdefault.leptonCuts.SUSY_LM9_Cern_1.root",
    "CERNdefault.leptonCuts.TTJets_madgraph_Cern_2.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_10.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_11.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_2.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_5.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_6.root",
    "CERNdefault.leptonCuts.WJets_madgraph_Cern_9.root",
    "CERNdefault.leptonCuts.ZJets_madgraph_Cern_2.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_11.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_12.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_13.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_14.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_18.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_20.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_21.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_22.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_23.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_24.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_26.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_27.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_3.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_11.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_12.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_13.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_14.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_15.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_16.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_17.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_18.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_19.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_21.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_23.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_24.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_25.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_26.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_28.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_29.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_2.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_30.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_31.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_32.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_33.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_34.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_35.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_37.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_38.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_39.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_3.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_40.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_41.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_42.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_43.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_44.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_45.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_46.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_47.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_48.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_49.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_4.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_50.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_51.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_52.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_6.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_7.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_8.root",
    "CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_9.root",
    "CERNdefault.looseCuts.QCD100to250_madgraph_Cern_10.root",
    "CERNdefault.looseCuts.QCD100to250_madgraph_Cern_13.root",
    "CERNdefault.looseCuts.QCD100to250_madgraph_Cern_14.root",
    "CERNdefault.looseCuts.QCD100to250_madgraph_Cern_4.root",
    "CERNdefault.looseCuts.QCD100to250_madgraph_Cern_5.root",
    "CERNdefault.looseCuts.WJets_madgraph_Cern_12.root",
    "CERNdefault.looseCuts.WJets_madgraph_Cern_2.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_11.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_13.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_14.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_15.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_16.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_17.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_18.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_19.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_1.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_21.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_22.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_23.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_26.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_27.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_28.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_29.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_2.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_3.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_5.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_6.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_7.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_8.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_9.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_16.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_17.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_18.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_19.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_21.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_23.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_25.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_26.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_29.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_2.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_31.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_32.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_34.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_35.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_37.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_39.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_41.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_42.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_43.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_44.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_47.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_48.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_49.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_4.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_51.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_52.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_6.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_7.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_8.root",
    "CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_9.root",
    "CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_10.root",
    "CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_11.root",
    "CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_2.root",
    "CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_8.root",
    "CERNparticleFlow.leptonCuts.QCD250to500_madgraph_Cern_2.root",
    "CERNparticleFlow.leptonCuts.QCD250to500_madgraph_Cern_6.root",
    "CERNparticleFlow.leptonCuts.QCD500to1000_madgraph_Cern_7.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_10.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_11.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_3.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_4.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_7.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_8.root",
    "CERNparticleFlow.leptonCuts.QCDpt15_Cern_9.root",
    "CERNparticleFlow.leptonCuts.QCDpt170_Cern_1.root",
    "CERNparticleFlow.leptonCuts.QCDpt170_Cern_3.root",
    "CERNparticleFlow.leptonCuts.QCDpt170_Cern_6.root",
    "CERNparticleFlow.leptonCuts.QCDpt30_Cern_2.root",
    "CERNparticleFlow.leptonCuts.QCDpt30_Cern_3.root",
    "CERNparticleFlow.leptonCuts.QCDpt30_Cern_4.root",
    "CERNparticleFlow.leptonCuts.QCDpt30_Cern_5.root",
    "CERNparticleFlow.leptonCuts.QCDpt80_Cern_1.root",
    "CERNparticleFlow.leptonCuts.QCDpt80_Cern_2.root",
    "CERNparticleFlow.leptonCuts.QCDpt80_Cern_4.root",
    "CERNparticleFlow.leptonCuts.QCDpt80_Cern_5.root"
                    ]
    compareList = {'CERNdefault': {'leptonCuts': {'EMenrichedQCDpt20_30_Cern': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 1, 20, 21, 22, 23,
                                                              24, 25, 26, 27, 28, 29, 2, 3, 4, 6, 8, 9],
                                'EMenrichedQCDpt30_80_Cern': [11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 26, 28, 29, 2,
                                                              30, 31, 32, 33, 34, 35, 37, 38, 39, 3, 40, 41, 42, 43, 44, 45, 46,
                                                              47, 48, 49, 4, 50, 51, 52, 6, 7, 8, 9],
                                'QCD1000toInf_madgraph_Cern': [1, 2],
                                'QCD100to250_madgraph_Cern': [10, 13, 14, 16, 17, 2, 3, 7],
                                'QCD250to500_madgraph_Cern': [1, 3, 6, 7],
                                'QCD500to1000_madgraph_Cern': [1, 2, 3, 4, 5, 6, 7],
                                'QCDpt15_Cern': [10, 11, 2, 5, 6, 8, 9],
                                'QCDpt170_Cern': [3, 4, 6],
                                'QCDpt300_Cern': [2, 3],
                                'QCDpt30_Cern': [2, 3, 5],
                                'QCDpt470_Cern': [1, 2, 3, 4],
                                'QCDpt800_Cern': [1, 3],
                                'SUSY_LM0_Cern': [1],
                                'SUSY_LM10_Cern': [1],
                                'SUSY_LM11_Cern': [1],
                                'SUSY_LM1_Cern': [1],
                                'SUSY_LM2_Cern': [1],
                                'SUSY_LM3_Cern': [1],
                                'SUSY_LM4_Cern': [1],
                                'SUSY_LM5_Cern': [1],
                                'SUSY_LM6_Cern': [1],
                                'SUSY_LM7_Cern': [1],
                                'SUSY_LM9_Cern': [1],
                                'TTJets_madgraph_Cern': [2],
                                'WJets_madgraph_Cern': [10, 11, 2, 5, 6, 9],
                                'ZJets_madgraph_Cern': [2]},
                 'looseCuts': {'EMenrichedQCDpt20_30_Cern': [11, 12, 13, 14, 18, 20, 21, 22, 23, 24, 26, 27, 3],
                               'EMenrichedQCDpt30_80_Cern': [11, 12, 13, 14, 15, 16, 17, 18, 19, 21, 23, 24, 25, 26, 28, 29,
                                                             2, 30, 31, 32, 33, 34, 35, 37, 38, 39, 3, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 4, 50, 51, 52, 6, 7, 8, 9],
                               'QCD100to250_madgraph_Cern': [10, 13, 14, 4, 5],
                               'WJets_madgraph_Cern': [12, 2]}},
 'CERNparticleFlow': {'leptonCuts': {'EMenrichedQCDpt20_30_Cern': [11, 13, 14, 15, 16, 17, 18, 19, 1, 21, 22, 23, 26, 27, 28, 29, 2, 3, 5, 6, 7, 8, 9],
                                     'EMenrichedQCDpt30_80_Cern': [16, 17, 18, 19, 21, 23, 25, 26, 29, 2, 31, 32, 34, 35, 37, 39, 41, 42, 43, 44, 47, 48, 49, 4, 51, 52, 6, 7, 8, 9],
                                     'QCD100to250_madgraph_Cern': [10, 11, 2, 8],
                                     'QCD250to500_madgraph_Cern': [2, 6],
                                     'QCD500to1000_madgraph_Cern': [7],
                                     'QCDpt15_Cern': [10, 11, 3, 4, 7, 8, 9],
                                     'QCDpt170_Cern': [1, 3, 6],
                                     'QCDpt30_Cern': [2, 3, 4, 5],
                                     'QCDpt80_Cern': [1, 2, 4, 5]}}}

testHistoListStrings = ['CERNdefault: looseCuts: EMenrichedQCDpt30_80_Cern: 2-4, 6-9, 11-19, 21, 23-26, 28-35, 37-52',
 '                        WJets_madgraph_Cern: 2, 12',
 '                        QCD100to250_madgraph_Cern: 4, 5, 10, 13, 14',
 '                        EMenrichedQCDpt20_30_Cern: 3, 11-14, 18, 20-24, 26, 27',
 'CERNdefault: leptonCuts: QCDpt170_Cern: 3, 4, 6',
 '                         QCD250to500_madgraph_Cern: 1, 3, 6, 7',
 '                         SUSY_LM5_Cern: 1',
 '                         SUSY_LM2_Cern: 1',
 '                         SUSY_LM4_Cern: 1',
 '                         SUSY_LM6_Cern: 1',
 '                         EMenrichedQCDpt20_30_Cern: 1-4, 6, 8-29',
 '                         QCD100to250_madgraph_Cern: 2, 3, 7, 10, 13, 14, 16, 17',
 '                         TTJets_madgraph_Cern: 2',
 '                         ZJets_madgraph_Cern: 2',
 '                         QCD500to1000_madgraph_Cern: 1-7',
 '                         QCDpt15_Cern: 2, 5, 6, 8-11',
 '                         QCDpt30_Cern: 2, 3, 5',
 '                         SUSY_LM9_Cern: 1',
 '                         SUSY_LM11_Cern: 1',
 '                         SUSY_LM10_Cern: 1',
 '                         QCD1000toInf_madgraph_Cern: 1, 2',
 '                         QCDpt470_Cern: 1-4',
 '                         SUSY_LM3_Cern: 1',
 '                         QCDpt300_Cern: 2, 3',
 '                         SUSY_LM0_Cern: 1',
 '                         EMenrichedQCDpt30_80_Cern: 2-4, 6-9, 11-19, 21, 23-26, 28-35, 37-52',
 '                         QCDpt800_Cern: 1, 3',
 '                         SUSY_LM1_Cern: 1',
 '                         WJets_madgraph_Cern: 2, 5, 6, 9-11',
 '                         SUSY_LM7_Cern: 1',
 'CERNparticleFlow: leptonCuts: QCD100to250_madgraph_Cern: 2, 8, 10, 11',
 '                              QCD500to1000_madgraph_Cern: 7',
 '                              QCDpt15_Cern: 3, 4, 7-11',
 '                              QCD250to500_madgraph_Cern: 2, 6',
 '                              QCDpt30_Cern: 2-5',
 '                              QCDpt170_Cern: 1, 3, 6',
 '                              EMenrichedQCDpt30_80_Cern: 2, 4, 6-9, 16-19, 21, 23, 25, 26, 29, 31, 32, 34, 35, 37, 39, 41-44, 47-49, 51, 52',
 '                              QCDpt80_Cern: 1, 2, 4, 5',
 '                              EMenrichedQCDpt20_30_Cern: 1-3, 5-9, 11, 13-19, 21-23, 26-29']


haddCommands = """['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/looseCuts/CERNdefault.looseCuts_EMenrichedQCDpt30_80_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_12.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_15.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_19.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_24.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_25.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_28.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_29.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_30.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_31.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_32.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_33.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_34.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_35.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_37.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_38.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_39.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_40.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_41.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_42.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_43.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_44.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_45.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_46.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_47.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_48.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_49.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_50.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_51.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_52.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_7.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt30_80_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/looseCuts/CERNdefault.looseCuts_WJets_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.WJets_madgraph_Cern_12.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.WJets_madgraph_Cern_2.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/looseCuts/CERNdefault.looseCuts_QCD100to250_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.QCD100to250_madgraph_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.QCD100to250_madgraph_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.QCD100to250_madgraph_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.QCD100to250_madgraph_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.QCD100to250_madgraph_Cern_5.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/looseCuts/CERNdefault.looseCuts_EMenrichedQCDpt20_30_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_12.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_20.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_22.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_24.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_27.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.looseCuts.EMenrichedQCDpt20_30_Cern_3.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt170_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt170_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt170_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt170_Cern_6.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCD250to500_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD250to500_madgraph_Cern_7.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM5_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM5_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM2_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM2_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM4_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM4_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM6_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM6_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_EMenrichedQCDpt20_30_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_12.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_15.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_19.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_20.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_22.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_24.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_25.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_27.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_28.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_29.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt20_30_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCD100to250_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD100to250_madgraph_Cern_7.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_TTJets_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.TTJets_madgraph_Cern_2.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_ZJets_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.ZJets_madgraph_Cern_2.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCD500to1000_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_5.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD500to1000_madgraph_Cern_7.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt15_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_5.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt15_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt30_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt30_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt30_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt30_Cern_5.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM9_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM9_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM11_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM11_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM10_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM10_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCD1000toInf_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD1000toInf_madgraph_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCD1000toInf_madgraph_Cern_2.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt470_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt470_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt470_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt470_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt470_Cern_4.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM3_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM3_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt300_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt300_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt300_Cern_3.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM0_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM0_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_EMenrichedQCDpt30_80_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_12.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_15.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_19.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_24.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_25.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_28.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_29.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_30.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_31.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_32.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_33.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_34.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_35.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_37.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_38.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_39.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_40.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_41.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_42.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_43.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_44.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_45.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_46.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_47.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_48.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_49.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_50.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_51.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_52.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_7.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.EMenrichedQCDpt30_80_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_QCDpt800_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt800_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.QCDpt800_Cern_3.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM1_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM1_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_WJets_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_5.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.WJets_madgraph_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault/leptonCuts/CERNdefault.leptonCuts_SUSY_LM7_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNdefault.leptonCuts.SUSY_LM7_Cern_1.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_EMenrichedQCDpt30_80_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_19.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_25.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_29.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_31.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_32.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_34.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_35.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_37.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_39.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_41.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_42.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_43.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_44.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_47.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_48.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_49.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_51.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_52.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_7.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt30_80_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCD100to250_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD100to250_madgraph_Cern_8.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCDpt30_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt30_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt30_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt30_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt30_Cern_5.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCD500to1000_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD500to1000_madgraph_Cern_7.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCDpt15_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_10.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_7.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt15_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCD250to500_madgraph_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD250to500_madgraph_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCD250to500_madgraph_Cern_6.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCDpt80_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt80_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt80_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt80_Cern_4.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt80_Cern_5.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_EMenrichedQCDpt20_30_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_11.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_13.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_14.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_15.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_16.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_17.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_18.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_19.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_21.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_22.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_23.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_26.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_27.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_28.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_29.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_2.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_5.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_6.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_7.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_8.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.EMenrichedQCDpt20_30_Cern_9.root']
['hadd', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow/leptonCuts/CERNparticleFlow.leptonCuts_QCDpt170_Cern.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt170_Cern_1.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt170_Cern_3.root', '/data/projekte/superSymmetry/src/SubmitScripts/test/SUSY/PAT/Histos/CERNparticleFlow.leptonCuts.QCDpt170_Cern_6.root']
"""
