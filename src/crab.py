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
	if PublishName != '':
		repMap["PublishBlock"] = """storage_element = %(StageoutSite)s
user_remote_dir = %(user_remote_dir)s
publish_data = 1
publish_data_name = %(PublishName)s 
dbs_url_for_publication =%(dbsurl)s """ % repMap
	else:
		repMap["PublishBlock"] = """storage_element = %(storage_element)s
storage_path = /srm/managerv2?SFN=%(histogramstoragepath)s/%(theJob)s""" % repMap

	if settings.skimFromLocalDBS or PublishName == '':
		repMap["customDBSBlock"] = "dbs_url = %(dbsurl)s" % repMap

	txt = """[CRAB]
jobtype = cmssw
scheduler = glite
use_server = 1
#server_name = %(CrabServer)s
%(CRAB-AdditionsBlock)s

[CMSSW]
datasetpath = %(datasetpath)s
%(customDBSBlock)s
pset = %(ParameterSet)s
total_number_of_events = %(numEvents)s
events_per_job = %(nEventsPerJob)s
output_file = %(OutputFiles)s
#Not used at the moment, but can be used if quicker
#get_edm_output = 1
allow_NonProductionCMSSW = 1
%(CMSSW-AdditionsBlock)s

[USER]
ui_working_dir = %(workdir)s
copy_data = 1
%(PublishBlock)s
thresholdLevel = 70
eMail = %(email)s
%(USER-AdditionsBlock)s

[GRID]
virtual_organization = cms
group = dcms
%(GRID-AdditionsBlock)s

[CONDORG]
%(CONDORG-AdditionsBlock)s

[CAF]
%(CAF-AdditionsBlock)s
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
