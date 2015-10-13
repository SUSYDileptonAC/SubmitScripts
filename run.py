#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time, srmop, dbsop, subprocess, shutil
import py_compile
import configurator, getopt, threading, random, Queue
import src.crab as crab, src.analysis as analysis
from optparse import OptionParser


#from pfade import *
from src.mainConfig import MainConfig

#from configurator import config as cfg

# global variables
# not needed at the moment

def getOptparser():
  parser = OptionParser()
  parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                          help="Verbose mode.")
  parser.add_option("-n", "--dry-run", action="store_true", dest="dryrun", default=False,
                          help="Dry-run mode, no job submission.")
  parser.add_option("-g", "--grid", action="store_true", dest="grid", default=False,
                          help="Submit jobs to grid.")
  parser.add_option("-M", "--MVA", action="store_true", dest="mva", default=False,
                          help="Submit job including MVA dicriminator. No cuts are applied and TASK.mva is used to filter.")
  parser.add_option("-s", "--skims", action="store_true", dest="skim", default=False,
                          help="Define the skims to run. -s StewMuon10pb. No analysis is done.")
  parser.add_option("-u", "--update", action="store_true", dest="update", default=False,
                          help="To be used with -s to update the jobs.")
  parser.add_option("-c", "--create", action="store_true", dest="create", default=False,
                          help="To be used with -s to create the jobs.")
  parser.add_option("-F", "--famos", dest="famos", nargs=1,
                          help="Define the famos job to run. -F FastSim_LM9t175_sftsdkpyt_PAT. No analysis is done.")
  parser.add_option("-t", "--task", dest="tasks", action="append", default=[],
                          help="Set parameters of the job to TASK.")
  parser.add_option("-f", "--flag", dest="flag", nargs=1, default='test',
                          help="Set naming of the job to FLAG.")
  parser.add_option("-o", "--output", action="store_true", dest="output", default=False,
                          help="Get the output of the jobs from storage element.")
  #parser.add_option("-j", "--job", dest="job", nargs=1, default='LM9t175_sftsdkpyt',
  parser.add_option("-j", "--job", dest="job", nargs=1, default='SUSY_LM0_sftsht',
                          help="Submit the job.")
  parser.add_option("-a", "--all", action="store_true", dest="all", default=False,
                          help="Submit all jobs.")
  parser.add_option("-m", "--missing", action="store_true", dest="missing", default=False,
                          help="Submit all jobs where no output is returned.")
  parser.add_option("-l", "--luminosity", dest="lumi", nargs=1, default= -1,
                                  help="Luminosity in pb^{-1}.")
  parser.add_option("-H", "--HLT", dest="hlt", nargs=1, default='', #'"HLT_Mu9","HLT_Ele15_SW_L1R"',
                          help="HLT trigger bits to select events e.g, \"HLT_Mu9\",\"HLT_Ele15_SW_L1R\".")
  parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
  parser.add_option("-G", "--Groups", dest="Groups",
                          help="Groups of jobs to run from the master list. If neither of 'not' 'and' 'or' are present or is taken. Else boolean logic is observed")
  parser.add_option("--coreNumber", dest="coreNumber", default = -1,
                    help="use the ith core (i.e. the ith bunch of file in localFileList")
  return parser

# entry point: start script and parse command line options
def main(argv=None):
  if argv == None:
    argv = sys.argv[1:]

  global theVerbose
  global theDryrun
  global theSubmitmode
  global Skim
#  global theSkims
  global theFlag
  global theTasks
#  global theJob
  global theGetOutput
  global theMVA
  global theLuminosity
  global theHLT

  # for multi-threaded output fetching
  global theThreadId
  theThreadId = 1
  global theThreadJobQueue
  theThreadJobQueue = Queue.Queue(0)

  #create option parser
  parser = getOptparser()
  (opts, args) = parser.parse_args(argv)
  if opts.Config == []:
      opts.Config = [ "Input/default.ini" ]
  opts.lumi = int(opts.lumi)
  if opts.job.startswith(" "):
      opts.job = opts.job[1:]
  opts.job = opts.job.split(",")
  opts.flag = opts.flag.replace(" ", "")
  #set up ManiConfig singelton
  settings = MainConfig(opts.Config, opts)

  print 'Starting at: ' + time.asctime(time.localtime())
  print settings.CSA

  #initialize global options
  theVerbose = opts.verbose
  theDryrun = opts.dryrun
#  theSkim = opts.skim
  theFamos = opts.famos
  theFlag = opts.flag
  theTasks = opts.tasks
 # theJob = opts.job
  theGetOutput = opts.output
  theMVA = opts.mva
  theLuminosity = int(opts.lumi)
  theHLT = opts.hlt

  nonjobs = []
  if not opts.grid:
      theSubmitmode = 'local'
      if not opts.Groups == None:
        raise StandardError, "Groups option not available in local running!"
  else:
      if not (opts.all or opts.missing or (not opts.Groups == None)):
          theSubmitmode = 'grid'
      else:
          if not opts.job == []:
              print "WARNING: contents of opts.job is overwritten (atm this is common because of the default setting)"
              print "jobs were: %s" % opts.job
      if opts.all:
          theSubmitmode = 'gridall'
          opts.job = settings.masterConfig.sections()
      elif opts.missing and opts.Groups == None:
          theSubmitmode = 'gridmissing'
          opt.job = getAllMissing()
      elif not opts.Groups == None:
          if opts.missing:
              theSubmitmode = 'gridgroupsmissing'
          else:
              theSubmitmode = 'gridgroups'
          opts.job, nonjobs = getJobsFromGroups(opts.Groups, opts.missing, theFlag, theTasks)

  if theVerbose == True: print "submit mode is '%s'" % theSubmitmode
  if theVerbose == True: print "selected job(s) are:", ", ".join(opts.job)
  if theVerbose == True: print "Not submitted job(s) are:", ", ".join(nonjobs)

  # analysis
#FIXME: deprecated fetching stuff is handled elsewhere...
  if (theGetOutput == True):
      raise StandardError, "for now the fetching feature is disabled!"
#    print "Fetching output"
#    fetchOutputData(theJob);
#    if opts.all:
#        # fill job queue
#        for job in settings.masterConfig.sections():
#            theThreadJobQueue.put(job)
#        # start threads
#        for iThread in range(0, 7):
#            OutputFetchingThread().start()
#            # do not start all threads at the same time
#            time.sleep(0.5)
  if theFamos:
    print "Submitting famos"
    print theFamos
    submitFamos(theFamos)
  else:
    print "Starting analysis"
    if theVerbose == True:
      print 'Verbose mode active'
      if theMVA:
	         print '\033[1;31mRunning MVA filter: ' + settings.getTaskName(theTasks) + '.mva\033[1;m'
      print 'Job(s): %s' % opts.job
      print 'Task: ' + settings.getTaskName(theTasks)
      print 'Flag: ' + theFlag


  if theSubmitmode == 'local':
      if len(opts.job) > 1:
          raise "running many jobs locally is not supported! have to run on grid (-g) "
  psetPaths = []
  for job in opts.job:
      if settings.skim:
          if opts.update:
              #FIXME: deprecated
              raise StandardError, "This has not been implemented since multicrab switch!"
              configurator.updateJobs()
          elif opts.create:
              #FIXME: deprecated
              raise StandardError, "This has not been implemented since multicrab switch!"
              configurator.createJobs()
          else:
              psetPath = createSkimPSet(job)
              if not psetPath == None:
                  psetPaths.append(psetPath)
      else:
          psetPath = createAnalysisPSet(job)
          if settings.verbose:
              print "created: %s for job: %s" % (psetPath, job)
          if not psetPath == None:
              psetPaths.append(psetPath)

  #check if configfiles are valid
  for psetPath in psetPaths:
      py_compile.compile(psetPath, doraise=True)
      os.remove("%sc" % psetPath)



  if settings.grid:
      if settings.verbose: print "creating multicrab configfiles... ",
      crabCfgPaths = createCrabCfgs(opts.job, psetPaths)
      if settings.verbose: print "done. got: %s" % crabCfgPaths
      if not settings.dryrun:
          originPath = os.path.abspath(os.path.curdir)
          for crabCfgPath in crabCfgPaths:
		os.chdir(os.path.dirname(crabCfgPath))
		if settings.verbose: print "starting crab submit -c %s"%crabCfgPath.split("/")[-1]
		#print "starting crab submit -c %s"%crabCfgPath.split("/")[-1]
		subprocess.call(["crab submit -c %s"%crabCfgPath.split("/")[-1]], shell=True)
		os.chdir(originPath)

  else:
      if not settings.dryrun:
	  #copy additional input files to proper location to allow local running
	  psetPath = os.path.join(settings.analysispath, settings.flag, settings.getTaskName(settings.tasks), "psets")
	  import shutil, re
	  fileString = re.sub('[[]','',settings.additional_input_files)
	  fileString = re.sub('[]]','',fileString)
	  fileString = re.sub('["]','',fileString)	  
	  for file in fileString.split(','):
	      shutil.copyfile(file,settings.analysispath+"/"+file.split("/")[-1])
          startLocalJob(psetPaths[0], opts.job[0])

  settings.tearDown()
  print 'Finished at: ' + time.asctime(time.localtime())

def createMulticrabConfig(jobs, psetPaths):
    settings = MainConfig()
    sessionPath = os.path.abspath(os.path.join(settings.getCrabDirectory(jobs[0]), ".."))

    datasetPathMode = 'localdbspath'
    if settings.skim and not settings.skimFromLocalDBS:
        datasetPathMode = 'datasetpath'

    publishName = ""
    if settings.skim:
        publishName = jobs[0]
        numEvents = settings.nSkimEvents

    #for now the crab.cfg is created from the first job...
    crabCfgPath = os.path.join(sessionPath, "crabConfig.py")
    multicrabCfgPath = os.path.join(sessionPath, "multicrab.cfg")
    #name of the job has to be empty since multicrab adds the jobname on its own
    crab.createCRABcfg("", psetPaths[0], sessionPath,
                       ", ".join(settings.getOutfiles(jobs[0])),
                       settings.masterConfig.get(jobs[0], 'localdbspath'),
                       str(analysis.LumiToNumber(jobs[0], settings.lumi)),
                       crabCfgPath, publishName
                       )
    #here multicrab ist created
    crab.createMULTICRABcfg(jobs, psetPaths, multicrabCfgPath, datasetPathMode)
    return (crabCfgPath, multicrabCfgPath)
    
def createCrabCfgs(jobs, psetPaths):
    settings = MainConfig()
    sessionPath = os.path.abspath(os.path.join(settings.getCrabDirectory(jobs[0]), ".."))

    datasetPathMode = 'localdbspath'
    if settings.skim and not settings.skimFromLocalDBS:
        datasetPathMode = 'datasetpath'

    publishName = ""
    #for now the crab.cfg is created from the first job...
    crabCfgPaths = []
    #name of the job has to be empty since multicrab adds the jobname on its own
    for jobIndex, job in enumerate(jobs):
	crabCfgPath = os.path.join(sessionPath, "crabConfig_%s.py"%job)    
	crabCfgPaths.append(crabCfgPath)
	outputFiles = []
	for index, file in enumerate(settings.getOutfiles(job)):
		if not index == 0:
			outputFiles.append(file)
	crab.createCRABcfg(job, psetPaths[jobIndex], sessionPath,
			outputFiles,
			settings.masterConfig.get(job, 'localdbspath'),
			str(analysis.LumiToNumber(job, settings.lumi)),
			crabCfgPath, publishName
			)
    #here multicrab ist created
    #crab.createMULTICRABcfg(jobs, psetPaths, multicrabCfgPath, datasetPathMode)
    return crabCfgPaths    

def createSkimPSet(job):
    ''' sets up the _cfg.py config-file for skimming'''
    settings = MainConfig(job=job)
    dataset = settings.masterConfig.get(job, 'datasetpath')
    if settings.skimFromLocalDBS:
        if not settings.masterConfig.has_option(job, 'localdbspath'):
            print "WARNING %s has no local DBS entry. skipping..." % job
            return
        dataset = settings.masterConfig.get(job, 'localdbspath')

    skimTemplate = os.path.abspath(settings.skimcfgname)
    if not os.path.exists(skimTemplate):
        raise StandardError, "could not find skim template: %s" % skimTemplate
    if settings.verbose == True: print 'Using ' + skimTemplate
    psetPath = os.path.join(settings.skimpath, settings.flag, "psets", os.path.split(skimTemplate)[1])

    if not os.path.exists(psetPath):
        if not os.path.exists(os.path.dirname(psetPath)):
            os.makedirs(os.path.dirname(psetPath))
        shutil.copy(skimTemplate, psetPath)
    return psetPath

def createAnalysisPSet(job, flag=None, tasks=None):
  ''' create files in the PSets directory '''
  settings = MainConfig(job=job)
  if flag == None: flag = settings.flag
  if tasks == None: tasks = settings.tasks
  # config file
  if settings.verbose == True: print 'Checking for local DBS path: ',
  if not settings.masterConfig.has_option(job, 'localdbspath'):
    print "\nWARNING: could not find job '%s' in masterConifg. not submitting anything ! " % job
  else:
    if settings.verbose == True:
      print settings.masterConfig.get(job, 'localdbspath')
      if (settings.masterConfig.has_option(job, 'numevents')):
        print 'Number of events: ' + settings.masterConfig.get(job, 'numevents')
      else:
        print 'Number of events: unknown'

      if (settings.masterConfig.has_option(job, 'localevents')):
        print 'Number of local events: ' + settings.masterConfig.get(job, 'localevents')
      else:
        print 'Number of local events: unknown'

      if (settings.masterConfig.has_option(job, 'crosssection')):
        print 'Analysing only local events: ' + str(analysis.LumiToNumber(job, settings.lumi))
      else:
        print 'No info about crosssection'

    # create cfg-file
    if settings.verbose == True: print 'Creating cfg file',
    nEvents = analysis.LumiToNumber(job, settings.lumi)
    psetContent = analysis.getPATPset(flag, job, '-1', tasks, settings.hlt, settings.mva)
    psetPath = os.path.join(settings.analysispath, flag, settings.getTaskName(tasks), "psets")
    if not os.path.exists(psetPath):
        os.makedirs(psetPath)
    psetPath = os.path.join(psetPath, "%s_%s_%s_cfg.py" % (flag, settings.getTaskName(tasks), job))
    if os.path.exists(psetPath):
        if settings.verbose == True: print ", it exists. overwriting:",
    psetFile = open(psetPath, "w")
    psetFile.write(psetContent)
    psetFile.close()
    if settings.verbose == True: print ":", psetPath
    return psetPath

def startLocalJob(pset, job, flag=None, tasks=None, MVA=None):
  settings = MainConfig(job=job)
  if flag == None: flag = settings.flag
  if tasks == None: tasks = settings.tasks
  #ME: Not sure what this is for.... 
  #if MVA == None: task = settings.mva

  originPath = os.path.abspath(os.path.curdir)
  # start job
  #print analysis.numbers(job)
  os.chdir(settings.analysispath)
  if theVerbose == True: print 'Starting job: ',
  print 'cmsRun ' + pset
  if MVA:
    shutil.copyfile(settings.analysispath + '/MVA/' + settings.getTaskName(tasks) + '.mva', settings.analysispath + '/' + settings.getTaskName(tasks) + '.mva')

  if theDryrun == False:
    subprocess.call(['cmsRun ' + pset], shell=True)
    if not os.path.exists(settings.localhistopath):
        os.makedirs(settings.localhistopath)
    for outFile in settings.getOutfiles(job):
		print outFile
    for outFile in settings.getOutfiles(job):
        shutil.move(os.path.join(settings.analysispath, outFile) ,
                    os.path.join(settings.localhistopath, outFile))
    if MVA:
      os.remove(settings.analysispath + '/' + settings.getTaskName(tasks) + '.mva')
  else:
    if theVerbose == True: print 'Dry-run mode: NOT starting local job: %s' % job
  os.chdir(originPath)

def submitFamos(job):
	print 'Submitting famos job ' + job
	crab.submitFamos(job, verbose=theVerbose, dryrun=theDryrun)

def checkAnalysisStatus():
    settings = MainConfig()
    f = open(settings.analysispath + '/analysis.list', 'r')
    analyzed = f.readlines()
    for n in range(len(analyzed)):
        crab.status(analyzed[n][:-1])
    f.close()

def checkSkimStatus():
    settings = MainConfig()
    f = open(settings.skimpath + '/skims.list', 'r')
    analyzed = f.readlines()
    for n in range(len(analyzed)):
        crab.status(analyzed[n][:-1])
    f.close()

# get all jobs
def getAllMissing(flag, task, MVA=False):
    i = 0
    result = []
    settings = MainConfig()
    all = len(settings.masterConfig.sections())
    for job in settings.masterConfig.sections():
	#fetch output before checking the file
        #fetchOutputData(job)
        i += 1
        fileName = settings.analysispath + '/Histos/' + flag + "." + task + "." + jobName + "_1.root"
        if theVerbose == True: print 'Checking for file ' + fileName + ' ... ',
        if os.path.exists(fileName) == False:
            if theVerbose == True: print 'not found'
            print '\033[1;34mMissing job ' + str(i) + ' of ' + str(all) + ': ' + job + '\033[m'
            result.append(job)
        else:
            if theVerbose == True: print 'found'
            print 'Not submitting job ' + str(i) + ' of ' + str(all)
    return result

# get job output
def fetchOutputData(job):
    settings = MainConfig(job=job)
    if theVerbose == True: print 'Fetching output data from job ' + job
    if settings.masterConfig.has_option(job, 'localdbspath'):
        #srmop.CopyHistos(job)
        srmop.CopyHistos1(job, theFlag, theTask)

# Thread class for output fetching
class OutputFetchingThread(threading.Thread):
    theId = 0
    def run(self):
        global theThreadId
        self.threadId = theThreadId
        theThreadId = theThreadId + 1
        if theVerbose == True: print "(thread " + str(self.threadId) + "): Thread started"

        while theThreadJobQueue.empty() == False:
            job = theThreadJobQueue.get()
            if (job != None):
                print "(thread " + str(self.threadId) + "): Now responsible for job " + job
                fetchOutputData(job)
            else:
                logOutput("(thread " + str(self.threadId) + "): Error: Job is empty")

        if theVerbose == True: print "(thread " + str(self.threadId) + "): Thread finished"

#helpers
def getJobsFromGroups(groupSelection, missing, flag, tasks):
    groupSelection = groupSelection.replace(", ", " or ")
    settings = MainConfig()
    result = []
    nonresult = []

    for jobName in settings.masterConfig.sections():
        if settings.inGroup(groupSelection, jobName):
            if settings.masterConfig.has_option(jobName, 'localevents') and settings.masterConfig.has_option(jobName, 'crosssection') and settings.masterConfig.has_option(jobName, 'kfactor') and settings.masterConfig.has_option(jobName, 'numevents') and settings.masterConfig.has_option(jobName, 'localdbspath'):
                if missing:
                    fileName = settings.localhistopath + "/" + flag + "_" + settings.getTaskName(tasks) + "_" + jobName + "_1.root"
                    if theVerbose == True: print 'Checking for file ' + fileName + ' ... ',
                    if os.path.exists(fileName) == False:
                        if theVerbose == True: print 'not found'
                        result.append(jobName)
                    else:
                        fileSize = os.path.getsize(fileName)
                        if float(fileSize) < float(settings.minFileSize):
                            if theVerbose == True: print "found, but too small with size %s" % (fileSize)
                            result.append(jobName)
                        else:
                            if theVerbose == True: print 'found'
                            nonresult.append(jobName)
                else:
                    result.append(jobName)
            else:
                nonresult.append(jobName)
    return result, nonresult

# start main script
if __name__ == '__main__':
    if False:
        import os.path
        originPath = os.path.abspath(os.path.curdir)
        #main(["-C Input/default.ini", "-n", "-v", "-j Upsilon3S"])
        os.chdir(originPath)
        #main(["-C Input/default.ini", "-n", "-g", "-v", "-j QCDpt80, SUSY_LM10"])
        os.chdir(originPath)
        #main(["-C Input/default.ini", "-n", "-a", "-g", "-v"])
        os.chdir(originPath)
        main(["-C Input/default.ini", "-n", "-G LM9 and Summer08", "-g"])
        os.chdir(originPath)
        #main([ "-C Input/default.ini", "-G LM9", "-n", "-g", "-s", "-f _brot"])
    else:
        main()

################# UNITTESTS #################
import unittest
import optparse
class statusTest(unittest.TestCase):
    unsaveOverride = True
    def setUp(self):
        self.originPath = os.path.abspath(os.path.curdir)
        parser = getOptparser()
        (opts, args) = parser.parse_args(["-funittest", "-tbaseCuts", "-totherCuts"])

        MainConfig([ "unittest/Input/default.ini" ], opts)

    def tearDown(self):
        MainConfig().tearDown()
        os.chdir(self.originPath)

    def testCreatePset(self):
        settings = MainConfig()
        flag = settings.flag
        taskName = settings.getTaskName()
        job = "SUSY_LM0_Cern"
        psetPath = os.path.join(settings.analysispath, flag, taskName, "psets", "%s.%s.%s_cfg.py" % (flag, taskName, job))
        if os.path.exists(psetPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % psetPath)

        psetPathResult = createAnalysisPSet(job, flag, settings.tasks)

        self.__comapreFile(psetPathResult, "unittest/reference/unittest.baseCutsotherCuts.SUSY_LM0_Cern_cfg.py")

        os.remove(psetPath)

    def testCreateSkimPSet(self):
        settings = MainConfig()
        psetPath = os.path.join(settings.skimpath, "unittest", "psets", os.path.split(settings.skimcfgname)[1])
        if os.path.exists(psetPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % psetPath)
        psetPathResult = createSkimPSet("SUSY_LM0_Cern")

        self.assertTrue(psetPathResult == psetPath, "Paths not the same:\n %s\n %s" % (psetPathResult, psetPath))
        self.__comapreFile(psetPathResult, psetPath)

        os.remove(psetPath)

    def testCreateMulticrabConfig(self):
        settings = MainConfig()
        flag = settings.flag
        taskName = settings.getTaskName()

        crabPath = os.path.join(settings.analysispath, flag, taskName, "crab.cfg")
        if os.path.exists(crabPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % crabPath)
        multicrabPath = os.path.join(settings.analysispath, flag, taskName, "multicrab.cfg")
        if os.path.exists(multicrabPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % multicrabPath)

        jobs = ["SUSY_LM0_Cern", "SUSY_LM9_Cern"]
        #no real nanmes or files here!
        psetPaths = [ os.path.join(settings.analysispath, flag, taskName, "psets", "%s_cfg.py" % job) for job in jobs]

        (crabPathResult, multicrabPathResult) = createMulticrabConfig(jobs, psetPaths)
        self.assertEquals(crabPathResult, crabPath)
        self.assertEquals(multicrabPathResult, multicrabPath)

        self.__comapreFile(crabPath, "unittest/reference/crab.cfg")
        os.remove(crabPath)
        self.__comapreFile(multicrabPath, "unittest/reference/multicrab.cfg")
        os.remove(multicrabPath)

    def testCreateMulticrabSkimConfig(self):
        settings = MainConfig()
        settings.getMap()["skim"] = True
        flag = settings.flag
        task = settings.tasks

#FIXME: not shure why the "unittest" needs to be there... 
        crabPath = os.path.join(settings.skimpath, "unittest", "crab.cfg")
        if os.path.exists(crabPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % crabPath)
        multicrabPath = os.path.join(settings.skimpath, "unittest", "multicrab.cfg")
        if os.path.exists(multicrabPath) and not self.unsaveOverride:
            self.fail("the file: '%s' is in the way ! " % multicrabPath)

        jobs = ["SUSY_LM0_Cern", "SUSY_LM9_Cern"]
        #no real nanmes or files here!
        psetPaths = [ os.path.join(settings.skimpath, "patLayer1_fromSummer08redigi_V5j_cfg.py") for job in jobs]

        (crabPathResult, multicrabPathResult) = createMulticrabConfig(jobs, psetPaths)
        self.assertTrue(crabPathResult == crabPath, "Paths not the same:\n %s\n %s" % (crabPathResult, crabPath))
        self.assertTrue(multicrabPathResult == multicrabPath, "Paths not the same:\n %s\n %s" % (multicrabPathResult, multicrabPath))

        self.__comapreFile(crabPath, "unittest/reference/skim-crab.cfg")
        os.remove(crabPath)
        self.__comapreFile(multicrabPath, "unittest/reference/skim-multicrab.cfg")
        os.remove(multicrabPath)

    def __comapreFile(self, resPath, refPath):
        resFile = open(resPath, "r")
        res = resFile.read()
        resFile.close()

        refFile = open(refPath, "r")
        ref = refFile.read()
        refFile.close()

        lineNo = 0
        for (resLine, refLine) in zip(res.splitlines(), ref.splitlines()):
            self.assertTrue(resLine == refLine, "Line %s:\n'%s'\n'%s'" % (lineNo, resLine, refLine))
            lineNo += 1



