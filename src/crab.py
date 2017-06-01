# -*- coding: utf-8 -*-
### adapting crab.py to use CRAB3, October 2014 Jan-F. Schulte

import os, subprocess, shutil
#, srmop
import analysis
from mainConfig import MainConfig
from analysis import LumiToNumber

def createCRABcfg(Job, Pset, WorkDir, OutputFiles, DBSpath, numEvents, crabcfg, PublishName=''):
	#TODO get rid of last if statement
	#probably factorize in three sections [CRAB], [CMSSW], [USER]
	settings = MainConfig()
	repMap = {
		"theJob": Job,
		"ParameterSet": Pset,
		"OutputFiles": OutputFiles,
		"datasetpath": DBSpath,
		"numEvents": numEvents,
		"workdir": WorkDir,
		"PublishName": PublishName,
		"customDBSBlock": "#no custom DBS",
		"GRID-AdditionsBlock": ""
	}
	#put CMSSW.increment_seeds=generator,VtxSmeared for production
	repMap.update(settings.getMap())
	repMap.update(settings.crabAdditionsBlocks)
	if not repMap["lumi_mask"] == "":
		repMap["nUnits"] = repMap["lumis_per_job"]
	else:
		if repMap["splitting"] == "FileBased":
			repMap["nUnits"] = repMap["files_per_job"]
		else:
			repMap["nUnits"] = repMap["events_per_job"]
	repMap["InFiles"] = repMap["additional_input_files"]


	txt = """from WMCore.Configuration import Configuration
config = Configuration()
	
config.section_("General")
	
config.General.requestName = "%(theJob)s"
config.General.workArea = "%(workdir)s"	
config.General.transferOutputs = True
config.General.transferLogs = False
	
%(General-AdditionsBlock)s	
	
config.section_("JobType")

config.JobType.pluginName = "Analysis"
config.JobType.psetName = "%(ParameterSet)s"
config.JobType.inputFiles = %(InFiles)s
config.JobType.outputFiles = %(OutputFiles)s
config.JobType.allowUndistributedCMSSW = True
%(JobType-AdditionsBlock)s

config.section_("Data")

config.Data.inputDataset = "%(datasetpath)s"
config.Data.lumiMask = "%(lumi_mask)s"
config.Data.inputDBS = "%(inputDBS)s"
config.Data.splitting = "%(splitting)s"
config.Data.unitsPerJob = %(nUnits)s
config.Data.totalUnits = %(numEvents)s
config.Data.publication = %(publish)s
config.Data.publishDBS = "%(pubDBSURL)s"
config.Data.outputDatasetTag = "%(theJob)s"
config.Data.ignoreLocality = True
config.Data.outLFNDirBase = "%(histogramstoragepath)s/%(theJob)s"

%(Data-AdditionsBlock)s

config.section_("Site")

config.Site.storageSite = "%(StageoutSite)s"
config.Site.blacklist = ["T3_MX_Cinvestav","T2_UA_KIPT","T3_IT_Perugia","T2_US_Vanderbilt"]
%(Site-AdditionsBlock)s

config.section_("User")

config.User.voGroup = "dcms"
%(User-AdditionsBlock)s

config.section_("Debug")

%(Debug-AdditionsBlock)s

""" % repMap
 	if not os.path.exists(os.path.dirname(crabcfg)):
 		os.makedirs(os.path.dirname(crabcfg))

	f = open(crabcfg, 'w')
	f.write(txt)
	f.close()
	return txt

def createMULTICRABcfg(jobs, psetPaths, multicrabCfgPath, datasetPathMode='localdbspath', crabCfgPath="crab.cfg"):
	'''create actual multicrab.cfg'''
	settings = MainConfig()
	repMap = {"crabCfgPath": crabCfgPath}
	result = """
[MULTICRAB]
cfg=%(crabCfgPath)s

[COMMON]
""" % repMap
	perJobBlock = """
#-----------------
[%(name)s]
CMSSW.datasetpath = %(datasetpath)s 
CMSSW.pset = %(pset)s 
CMSSW.output_file = %(output_file)s 
CMSSW.total_number_of_events = %(number_events)s 
%(additions)s

%(publishBlock)s
"""

	for (job, psetPath) in zip(jobs, psetPaths):
		repMap.update({
						"name":job,
						"pset":psetPath,
						"output_file":", ".join(settings.getOutfiles(job)),
						"number_events":analysis.LumiToNumber(job, settings.lumi),
						"histogramstoragepath": settings.histogramstoragepath,
						"flag":settings.flag,
						"additions":"",
				 })

		if settings.skim:
			repMap["publishBlock"] = "USER.publish_data_name = %(name)s_%(flag)s" % repMap
		else:
			#not needed multicrab does this on its own!
			#repMap["publishBlock"] = "USER.user_remote_dir = %(histogramstoragepath)s/%(name)s" % repMap
			repMap["publishBlock"] = ""

		#if settings.masterConfig.has_option(job, "dbs_url"):
			#print settings.masterConfig.get(job, "dbs_url")
			#repMap["additions"] += "CMSSW.dbs_url = %s\n"%settings.masterConfig.get(job, "dbs_url")
		if not settings.masterConfig.has_option(job, datasetPathMode):
			print "WARNING: '%s' has no dataset path set. skipping job!" % (job)
		else:
			repMap["datasetpath"] = settings.masterConfig.get(job, datasetPathMode)
			result += perJobBlock % repMap

	if not os.path.exists(os.path.dirname(multicrabCfgPath)):
 		os.makedirs(os.path.dirname(multicrabCfgPath))

	multicrabFile = open(multicrabCfgPath, "w")
	multicrabFile.write(result)
	multicrabFile.close()

	return result

#FIXME: depricated by multicrab
def submitAnalysis(flag, pset, job, task, localDBS, nEv='-1', AddInput='', verbose=False, dryrun=False):
	settings = MainConfig()
	crabdir = settings.getCrabDirectory(job, task, flag)

	# delete existing crab directory
	if os.path.exists(crabdir):
		print "WARNING: jobpath '%s' does already exist." % crabdir
		if not dryrun:
			print "			 Deleting it..."
			shutil.rmtree(crabdir)

	# create new crab directory
	if (not os.path.exists(crabdir)):
		os.makedirs(crabdir)

	cfgname = os.path.abspath(os.path.join(crabdir, "..", "%s.%s.crab.cfg" % (flag, task)))
	outfiles = ", ".join(s2ettings.getOutfiles(job, task, flag)) #flag + '.' + task + '.' + job + '.root, ' + flag + '_' + task + '_' + job + '.log'
  	if verbose == True: print 'Creating CRAB cfg file: ' + cfgname,
	createCRABcfg(job, pset, crabdir, outfiles, localDBS, nEv, cfgname)
  	if verbose == True: print 'done'
  	if not dryrun:
  	  if verbose == True: print 'Submitting CRAB job into grid ...'
  	  subprocess.call(['crab -create -submit -cfg ' + cfgname], shell=True)
  	  analog = open(settings.analysispath + '/analysis.list', 'a')
  	  analog.write(crabdir + '\n')
  	  analog.close()

#FIXME: depricated by multicrab
def submitSkim(job, verbose=False, dryrun=True, nEv='-1', flag=""):
	settings = MainConfig()
	dataset = settings.masterConfig.get(job, 'datasetpath')
	if settings.skimFromLocalDBS:
		if not settings.masterConfig.has_option(job, 'localdbspath'):
			print "WARNING %s has no local DBS entry. skipping..." % job
			return
		dataset = settings.masterConfig.get(job, 'localdbspath')
	print 'Running: ' + job + " " + dataset
	cmsswcfg = settings.skimpath + '/' + settings.skimcfgname
	if not os.path.exists(cmsswcfg):
		raise StandardError, "could not find skim template: %s" % cmsswcfg

  	if verbose == True: print 'Using ' + cmsswcfg
	skimpath = settings.skimpath
	crabdir = os.path.join(skimpath, job)
	if os.path.exists(crabdir):
		deldir = raw_input(job + ' exists. Delete it? [Y,n]:')
		if deldir == 'Y':
			shutil.rmtree(crabdir)
			#srmop.DeleteAll(job)
		else:
			return
	os.mkdir(crabdir)
	crabcfg = settings.skimpath + '/CRABCFG/' + job + '.crab.cfg'
	outfiles = settings.skimoutputfiles
  	if verbose == True: print 'Creating CRAB cfg file: ' + crabcfg
	createCRABcfg(job, cmsswcfg, crabdir, outfiles, dataset, nEv, crabcfg, job + flag)

  	if verbose == True: print 'done'
  	# submit
	if not dryrun:
  		if verbose == True: print 'Submitting CRAB job into grid ...'
		subprocess.call(['crab -create -submit -cfg ' + crabcfg], shell=True)
		skimlog = open(settings.skimpath + '/skims.list', 'a')
		skimlog.write(settings.skimpath + '/' + job + '\n')
		skimlog.close()

def submitFamos(job, verbose=False, dryrun=True, nEv='50000'):
	settings = MainConfig()
	cmsswcfg = famospath + '/' + job + '.py'
	crabdir = os.path.join(famospath, job)
  	crabcfg = settings.famospath + '/CRABCFG/' + job + '.crab.cfg'
	outfiles = job + '.root'
  	print 'Job: ' + cmsswcfg
	if os.path.exists(crabdir):
		deldir = raw_input(job + ' exists. Delete it? [Y,n]:')
		if deldir == 'Y':
			shutil.rmtree(job)
			#srmop.DeleteAll(job)
		else:
			os.chdir(originPath)
			return
	os.mkdir(crabdir)
	if verbose == True: print 'Creating CRAB cfg file: ' + crabcfg,
	createCRABcfg(job, cmsswcfg, crabdir, outfiles, dataset, nEv, crabcfg, job)
  	if verbose == True: print 'done'
	if not dryrun:
  		# submit
  		if verbose == True: print 'Submitting CRAB job into grid ...'
		subprocess.call(['crab -create -cfg ' + crabcfg], shell=True)

def getAnaOutput():
	settings = MainConfig()
	f = open(os.path.join(settings.analysispath, 'analysis.list'), 'r')
	for line in f.readlines():
		getoutput(line.strip())
	f.close()

def status(path):
	subprocess.call(['crab -status -c ' + path], shell=True)

def resubmit(path):
	subprocess.call(['crab -resubmit all -c ' + path], shell=True)

def getoutput(path):
	subprocess.call(['crab -getoutput -c ' + path], shell=True)

def publish(path):
	subprocess.call(['crab -publish -c ' + path], shell=True)

def getHash(filename):
    theHash = subprocess.Popen(['edmConfigHash ' + filename], shell=True, stdout=subprocess.PIPE).communicate()[0].strip()
    return theHash
