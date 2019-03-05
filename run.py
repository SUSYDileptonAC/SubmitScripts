#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys, time, subprocess, shutil
import py_compile
import getopt, random
import src.crab as crab, src.analysis as analysis
from optparse import OptionParser


#from pfade import *
from src.mainConfig import MainConfig, BetterConfigParser

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
  parser.add_option("-t", "--task", dest="tasks", action="append", default=[],
                          help="Set parameters of the job to TASK.")
  parser.add_option("-f", "--flag", dest="flag", nargs=1, default='test',
                          help="Set naming of the job to FLAG.")
  parser.add_option("-m", "--mix", dest="mix", action="append", default=[],
                          help="Use mix of configs for job")
  parser.add_option("-j", "--job", dest="job", nargs=1, default='SUSY_LM0_sftsht',
                          help="Submit the job.")
  parser.add_option("-a", "--all", action="store_true", dest="all", default=False,
                          help="Submit all jobs.")
  parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
  parser.add_option("-G", "--Groups", dest="Groups",
                          help="Groups of jobs to run from the master list. If neither of 'not' 'and' 'or' are present or is taken. Else boolean logic is observed")
  return parser

# entry point: start script and parse command line options
def main(argv=None):
  if argv == None:
    argv = sys.argv[1:]

  global theVerbose
  global theDryrun
  global theSubmitmode
  global theFlag
  global theTasks
  
  #create option parser
  parser = getOptparser()
  (opts, args) = parser.parse_args(argv)
  
  
  # parse mix
  mixPathes = []
  mixTuples =  []
  for mix in opts.mix:
    
    if ":" in mix:
      mixPath, mixName = mix.split(":")
    else:
      mixPath, mixName = mix, "default"
    
    # every mix inherits from the "default" mix in its file
    if mixPath not in mixPathes and mixName != "default":
      mixPathes.append(mixPath)
      mixTuples.append( (mixPath.strip(), "default") )
    
    mixTuples.append( (mixPath.strip(), mixName) )

  
  for mixPath, mixName in mixTuples:
    mixParser = BetterConfigParser()
    mixParser.read(mixPath)
    
    try:
      mixOptions = dict(mixParser.items(mixName))
    except:
      print "ERROR: File %s has no section %s"%(mixPath, mixName)
      if mixName == "default":
        print "Every mix file needs a default section, even if it is left empty"
      raise
    
    if mixOptions.has_key("configs"):
      configsMix = mixOptions["configs"].split(" ")
      for conf in configsMix:
        opts.Config.append(conf)
        
    if mixOptions.has_key("tasks"):
      tasksMix = mixOptions["tasks"].split(" ")
      for task in tasksMix:
        opts.tasks.append(task)
        
    if mixOptions.has_key("groups"):
      groupsMix = mixOptions["groups"].strip()
      opts.Groups = groupsMix
      opts.grid = True
        
    if mixOptions.has_key("job"):
      jobMix = mixOptions["job"].strip()
      opts.job = jobMix
  

  if opts.Config == []:
      opts.Config = [ "Input/default102X.ini" ]
  if opts.job.startswith(" "):
      opts.job = opts.job[1:]
  opts.job = opts.job.split(",")
  opts.flag = opts.flag.replace(" ", "")
  #set up MainConfig singleton
  settings = MainConfig(opts.Config, opts)

  print 'Starting at: ' + time.asctime(time.localtime())
  print settings.CSA

  #initialize global options
  theVerbose = opts.verbose
  theDryrun = opts.dryrun
  theFlag = opts.flag
  theTasks = opts.tasks

  nonjobs = []
  if not opts.grid:
      theSubmitmode = 'local'
      if not opts.Groups == None:
        raise StandardError, "Groups option not available in local running!"
  else:
      if not (opts.all or (not opts.Groups == None)):
          theSubmitmode = 'grid'
      else:
          if not opts.job == []:
              print "WARNING: contents of opts.job is overwritten (atm this is common because of the default setting)"
              print "jobs were: %s" % opts.job
      if opts.all:
          theSubmitmode = 'gridall'
          opts.job = settings.masterConfig.sections()
      elif not opts.Groups == None:
          theSubmitmode = 'gridgroups'
          opts.job, nonjobs = getJobsFromGroups(opts.Groups, theFlag, theTasks)
          
  if theVerbose == True: print "submit mode is '%s'" % theSubmitmode
  if theVerbose == True: print "selected job(s) are:", ", ".join(opts.job)

  print "Starting analysis"
  if theVerbose == True:
      print 'Verbose mode active'
      print 'Job(s): %s' % opts.job
      print 'Task: ' + settings.getTaskName(theTasks)
      print 'Flag: ' + theFlag


  if theSubmitmode == 'local':
      if len(opts.job) > 1:
          raise "running many jobs locally is not supported! have to run on grid (-g) "
  psetPaths = []
  for job in opts.job:
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
      if settings.verbose: print "creating crab configfiles... ",
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


#helpers
def getJobsFromGroups(groupSelection, flag, tasks):
    groupSelection = groupSelection.replace(", ", " or ")
    settings = MainConfig()
    result = []
    nonresult = []

    for jobName in settings.masterConfig.sections():
        if settings.inGroup(groupSelection, jobName):
            if settings.masterConfig.has_option(jobName, 'localevents') and settings.masterConfig.has_option(jobName, 'crosssection') and settings.masterConfig.has_option(jobName, 'kfactor') and settings.masterConfig.has_option(jobName, 'numevents') and settings.masterConfig.has_option(jobName, 'datasetpath'):
                result.append(jobName)
            else:
                nonresult.append(jobName)
    return result, nonresult


def createCrabCfgs(jobs, psetPaths):
  settings = MainConfig()
  sessionPath = os.path.abspath(os.path.join(settings.getCrabDirectory(jobs[0]), ".."))

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
          settings.masterConfig.get(job, 'datasetpath'),
          crabCfgPath, publishName
        )
  return crabCfgPaths    

def createAnalysisPSet(job, flag=None, tasks=None):
  ''' create files in the PSets directory '''
  settings = MainConfig(job=job)
  if flag == None: flag = settings.flag
  if tasks == None: tasks = settings.tasks
  # config file
  if settings.verbose == True: print 'Checking for dataset path: ',
  if not settings.masterConfig.has_option(job, 'datasetpath'):
    print "\nWARNING: could not find job '%s' in masterConifg. not submitting anything ! " % job
  else:
    if settings.verbose == True:
      print settings.masterConfig.get(job, 'datasetpath')
      if (settings.masterConfig.has_option(job, 'numevents')):
        print 'Number of events: ' + settings.masterConfig.get(job, 'numevents')
      else:
        print 'Number of events: unknown'

      if (settings.masterConfig.has_option(job, 'localevents')):
        print 'Number of local events: ' + settings.masterConfig.get(job, 'localevents')
      else:
        print 'Number of local events: unknown'

    # create cfg-file
    if settings.verbose == True: print 'Creating cfg file',
    psetContent = analysis.getPATPset(flag, job, '-1', tasks)
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

def startLocalJob(pset, job, flag=None, tasks=None):
  settings = MainConfig(job=job)
  if flag == None: flag = settings.flag
  if tasks == None: tasks = settings.tasks
  
  originPath = os.path.abspath(os.path.curdir)
  # start job
  os.chdir(settings.analysispath)
  if theVerbose == True: print 'Starting job: ',
  print 'cmsRun ' + pset
  
  if theDryrun == False:
    subprocess.call(['cmsRun ' + pset], shell=True)
    if not os.path.exists(settings.localjobhistopath):
        os.makedirs(settings.localjobhistopath)
    for outFile in settings.getOutfiles(job):
      print outFile
    for outFile in settings.getOutfiles(job):
      shutil.move(os.path.join(settings.analysispath, outFile) ,
                  os.path.join(settings.localjobhistopath, outFile))
  else:
    if theVerbose == True: print 'Dry-run mode: NOT starting local job: %s' % job
  os.chdir(originPath)

# start main script
if __name__ == '__main__':
  main()



