import os, subprocess, re, glob
try:
	import dbsop
except ImportError:
	print "WARNING: no dbs support!"

from src.mainConfig import MainConfig

p = re.compile('TrigReport Events total =')

#get number of a log file asdfdjhf_123.log returns 123
def getNumberLog(file):
	settings = MainConfig()
	number = file[file.find(settings.logname) + len(settings.logname):file.find('.log')]
	return number

#get number of a root file asdfdjhf_123.root returns 123
def getNumberRoot(file):
	settings = MainConfig()
	number = file[file.find(settings.filename) + len(settings.filename):file.find('.root')]
	return number

#search numbers out of a log file
def search(file):
	total = 0
	passed = 0
	f = open(file, 'r')
	for line in f:
		if p.match(line):
			m = p.match(line)
			total = int(line[line.find('total = ') + 8:line.find(' passed')])
			passed = int(line[line.find('passed = ') + 9:line.find(' failed')])
	f.close()
	return total, passed

def checkAnalysisStatus(flag, job, task):
	settings = MainConfig(job=job)
	if os.path.exists("%(analysispath)s/Histos/%(flag)s.%(task)s.%(job)s_1.root" % settings.getMap()):
		return True
	else:
		return False

def LumiToNumber(job, lumi):
    settings = MainConfig(job=job)
    nEv = settings.defaultNumEvents
    if lumi == -1:
        return nEv
    if settings.masterConfig.has_option(job, 'localevents') and settings.masterConfig.has_option(job, 'crosssection') and settings.masterConfig.has_option(job, 'kfactor') and settings.masterConfig.has_option(job, 'numevents'):
        nEvAna = int(float(settings.masterConfig.get(job, 'localevents')) * float(settings.masterConfig.get(job, 'crosssection')) * float(settings.masterConfig.get(job, 'kfactor')) * lumi / float(settings.masterConfig.get(job, 'numevents')))
        if nEvAna < int(settings.masterConfig.get(job, 'localevents')):
            nEv = nEvAna
        else:
            print "WARNING: '%s' has not enough events in the dataset. Setting number of events to -1!" % (job)
    else:
        print "WARNING: '%s' has no kfactor, xsec, numevents, localevents set! Setting number of events to -1!" % (job)
    return nEv

#create a quiet message logger
def MessageLogger(analogname):
	txt = """
process.options = cms.untracked.PSet(\n
     wantSummary = cms.untracked.bool(True),
)
process.MessageLogger = cms.Service('MessageLogger',
  %(analogname)s = cms.untracked.PSet( 
     INFO = cms.untracked.PSet(
          limit = cms.untracked.int32(0)
     ),
     FwkReport = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          reportEvery = cms.untracked.int32(1000),
          limit = cms.untracked.int32(1000)
     ),
     default = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(100)
     ),
     Root_NoDictionary = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(0)
     ),
     FwkJob = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          limit = cms.untracked.int32(0)
     ),
     FwkSummary = cms.untracked.PSet(
          optionalPSet = cms.untracked.bool(True),               
          reportEvery = cms.untracked.int32(1),
          limit = cms.untracked.int32(10000000)
     ),
     threshold = cms.untracked.string('INFO')
  ),
  destinations = cms.untracked.vstring('%(analogname)s')
)
""" % {"analogname":analogname}
	return txt

#create a PoolSource from datapath/job/*.root files where a log is present
def poolSourceGrid(job, n):
	settings = MainConfig(job=job)
	txt = 'process.source = cms.Source(\'PoolSource\', \n'
    ##################Fixme: How to handle this on data
	txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
	txt += '     fileNames = cms.untracked.vstring('
	txt += ')\n'
	txt += ')\n\n'
	txt += 'process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(' + n + '))\n\n'
	#txt += 'eventsToProcess = cms.untracked.VEventRange(195399:3175301-195399:3175301)\n\n'
	return txt

def poolSourceLocal(job, n):
	settings = MainConfig(job=job)
#	txt = 'process.source = cms.Source(\'PoolSource\', \n'

    ##################Fixme: How to handle this on data
#	txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
#	txt += "eventsToProcess = cms.untracked.VEventRange('1:4165-1:4165'),\n"
#	txt += '     fileNames = cms.untracked.vstring('
	files = glob.glob("%(localdatapath)s/" % settings.getMap() + job + "/*.root")
	files = ["file:%s" % i for i in files]
	if settings.getMap()["masterConfig"].has_option(job, "localListPath"):
		localListPath = settings.getMap()["masterConfig"].get(job, "localListPath")
		listFile = open(localListPath, "r")
		files = ["dcap://grid-dcap.physik.rwth-aachen.de/pnfs/physik.rwth-aachen.de/cms/%s" % i for i in
			 listFile.read().split()]
		listFile.close()
	#	print "#####", settings.numCores, settings.coreNumber
	if int(settings.coreNumber) > 0:
		files = files[int((int(settings.coreNumber) - 1) * 1. / int(settings.numCores) * len(files)):
			      int(min(1., (int(settings.coreNumber)) * 1. / int(settings.numCores)) * len(files))]
		print "processing batch %s/%s (%i files)" % (settings.coreNumber, settings.numCores, len(files))

	txt = "fileList = %s\n" % files

	if settings.verbose: print "running localy on %i files in '%s'" % (len(files), "%(localdatapath)s/" % settings.getMap() + job)
	#if settings.verbose == True: print "%(localdatapath)s/" % settings.getMap() + job + "/*.root"

	#txt += ",\n".join(["\t\t'%s'" % file for file in files])
	txt += 'process.source = cms.Source(\'PoolSource\', \n'

	##################Fixme: How to handle this on data                                                                    txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
	#       txt += "eventsToProcess = cms.untracked.VEventRange('1:4165-1:4165'),\n"
	txt += '     fileNames = cms.untracked.vstring(fileList),\n'
	txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
	#for file in files:
	#	txt += '\'file:' + file + '\','
	#txt = txt[:-1] # remove the last comma
#	txt += ')\n'
	txt += ')\n\n'
	cmsswBlocks = settings.getMap()["crabAdditionsBlocks"]["Data-AdditionsBlock"].splitlines()
	jsonPath = None
	for cmsswBlock in cmsswBlocks:
		if "lumi_mask" in cmsswBlock:
			jsonPath = cmsswBlock.split("=")[-1].strip()

	if not jsonPath is None:
		if settings.verbose: print "using json file: '%s'" % jsonPath
		txt += """
import FWCore.PythonUtilities.LumiList as LumiList
#import PhysicsTools.PythonAnalysis.LumiList as LumiList
myLumis = LumiList.LumiList(filename = '%s').getCMSSWString().split(',')
process.source.lumisToProcess = cms.untracked.VLuminosityBlockRange()
process.source.lumisToProcess.extend(myLumis)
""" % jsonPath

	txt += 'process.maxEvents = cms.untracked.PSet( input = cms.untracked.int32(' + n + '))\n\n'
	return txt

#create a HLT filter
def createHLTFilter(HLT):
	#TODO hardcoded HLT Bits
	txt = 'process.LeptonHLT = cms.EDFilter("HLTHighLevel",\n'
    	txt += 'HLTPaths = cms.vstring(' + HLT + '),\n'
	txt += 'andOr = cms.bool(True),\n'
	txt += 'TriggerResultsTag = cms.InputTag("TriggerResults","","HLT")\n'
	txt += ')\n\n'
	return txt


def createMVAFilter(MVA):
	'''create a MVA filter'''

	#TODO hardcoded alberts stuff
	txt = 'process.load(\'AlbertBursche.ApplyMVA.Cuts\')\n\n'
	txt += 'process.filter = cms.EDFilter(\'ApplyMVA\',\n'
	txt += 'mvaFileName = cms.untracked.string(\'' + MVA + '.mva\'),\n'
        f = open(analysispath + '/MVA/' + MVA, 'r')
	txt += f.read()
	f.close()
	txt += ')\n\n'
	return txt


def TFileService(file):
	'''create a TFileService with output = file'''

	txt = 'process.TFileService = cms.Service(\'TFileService\', closeFileFast = cms.untracked.bool(True), fileName = cms.string(\'' + file + '\'))\n\n'
	return txt

def getOutputModule(path, taskName):
	  ''' create an output module to store created products in'''
	  settings = MainConfig()
	  result = ""
	  repMap = {"path":path,
		    "commands":"",
		    "SelectEvents":""}
	  commands = ["    'drop *'"]
	  if not settings.selectEvents == "":
		  selectingPathName = "%s%sPath" % (taskName, settings.selectEvents)
		  if settings.selectEvents == "activeFilters":
			  selectingPathName = "%sPath" % (taskName)
		  repMap["SelectEvents"] = """
   SelectEvents = cms.untracked.PSet( 
      SelectEvents = cms.vstring('%s')
   ),""" % selectingPathName

	  if not (settings.drop == [] and settings.keep == []):
	  	for product in settings.drop:
	  		commands.append("'drop %s'" % product)
		for product in settings.keep:
	  		commands.append("'keep %s'" % product)

	  	repMap["commands"] = ",\n    ".join(commands)

	  	result = """
process.out = cms.OutputModule("PoolOutputModule",
  fileName = cms.untracked.string('%(path)s'),
%(SelectEvents)s
  outputCommands = cms.untracked.vstring(
%(commands)s
  )
)
process.outpath = cms.EndPath(process.out)
""" % repMap
	  return result

def makePATConfig(flag, job, n, task, MC, Grid, Weighted, HLT, MVA=False):
	'''make a PAT cfg file for SUSYDiLepton Analysis'''
	#FIXME: variable 'Grid is not used anymore!'
	settings = MainConfig(job=job)
	txt = getPATPset(flag, job, n, task, MC, Weighted, HLT, MVA=False)
	repMap = {
		"flag": flag,
		"taskName":task,
		"job":job
		}
	if Grid:
		cfgname = settings.analysispath + "/CMSSWCFG/%(flag)s%(taskName)s.%(job)s.grid.py" % repMap
	if not Grid:
		cfgname = settings.analysispath + "/CMSSWCFG/%(flag)s%(taskName)s.%(job)s.local.py" % repMap
	f = open(cfgname, 'w')
	f.write(txt)
	f.close()
	return cfgname

def __createCounters(taskName, taskProducers):
	settings = MainConfig()
	result = """
from SuSyAachen.Histograms.triggerResultsCounter_cfi import triggerResultsCounter
process.%sCounters = triggerResultsCounter.clone( prefix = ['%s', '%s'], count = cms.VPSet() )
""" % (taskName, taskName + "Path" , "filterPathFor" + taskName)
	taskCounters = {}
	for sequence in taskProducers:
		result += "process.%sCounters.count.append( cms.PSet(name = cms.string('%s'), triggerNames = cms.vstring('%s') ) )\n" % (taskName,
														"%s counts for %s" % (taskName, sequence),
														"', '".join([ i[len(taskName):] for i in taskProducers[sequence]]))
	return result

def createTask(name, job):
	'create config-file snippet for a given taskname'
	from re import sub
	settings = MainConfig(job=job)
	defaultSrcName = "src"

	result = """#--- Task: %s\n""" % name
	taskProducers = {}
	rawTask = settings.getRawTask(name, {"isMC": settings.monteCarloAvailable})
	for sequence in rawTask:
		if not (sequence in ["activeFilters", "additionalFilters", "order"]):
			result += "import SuSyAachen.Skimming.defaults.%s_cfi\n" % sequence

			inputCollections = {}
			producerNum = 0
			for producer in rawTask[sequence]:
				repMap = {
						  "sequence": sequence,
						  "task":name,
						  "name": "%s%s" % (sequence, producerNum),
						  "selector": "defaultSelector",
						  "attributes": ""
						  }
				srcAttributes = [defaultSrcName]
				if "srcNames" in producer:
					srcAttributes = producer["srcNames"].split()
					if defaultSrcName in inputCollections:
						inputCollections = { srcAttributes[0] : inputCollections[ defaultSrcName] }

				for srcAttribute in srcAttributes:
					if srcAttribute in producer:
						if type(producer[srcAttribute]) == type(""):# and producer[srcAttribute].startswith("(") and producer[srcAttribute].endswith(")"): # note: could go for regexp for really bad cornercases...
							def repalceOnFlyProducer(matchobj):
								onFlyProducerName = None
								if len(matchobj.groups()) == 1 and matchobj.group(1) in rawTask:
									onFlyProducerName = rawTask[matchobj.group(1)][-1]["name"]
								else:
									for onFlyProducer in rawTask[matchobj.group(1)]:
										if onFlyProducer["name"] == matchobj.group(2):
											onFlyProducerName = matchobj.group(2)
								return "%s%s" % (name, onFlyProducerName)
							if "." in producer[srcAttribute]:
								inputCollections[srcAttribute] = sub("\((.*?)\.(.*?)\)", repalceOnFlyProducer, producer[srcAttribute])
							else:
								inputCollections[srcAttribute] = sub("\((.*?)\)", repalceOnFlyProducer, producer[srcAttribute])
						else:
							inputCollections[srcAttribute] = producer[srcAttribute]

				if inputCollections == {}:
					raise StandardError, "could not find inputCollection(s) (%s) in '%s' of task '%s'" % (srcAttributes, sequence, name)

				for srcAttribute in srcAttributes:
					producer[srcAttribute] = inputCollections[srcAttribute]

				for attribute in producer:
					if not attribute in ["name", "selector", "skip", "srcNames"]:
						repMap["attributes"] += "	%s = %s,\n" % (attribute, repr(producer[attribute]))
				repMap.update(producer)

				result += """
process.%(task)s%(name)s = SuSyAachen.Skimming.defaults.%(sequence)s_cfi.%(selector)s.clone(
%(attributes)s)
""" % repMap
				producerNum += 1
				if not "skip" in producer or not producer["skip"]:
					inputCollections = {defaultSrcName : "%(task)s%(name)s" % repMap}
				if not sequence in taskProducers:
					taskProducers[sequence] = ["%(task)s%(name)s" % repMap]
				else:
					taskProducers[sequence].append("%(task)s%(name)s" % repMap)

	sortedTaskProducers = []
	if "order" in rawTask:
		"using order: %s" % rawTask["order"]
		for seq in rawTask["order"]:
			if not seq in taskProducers:
				raise StandardError, "sequence '%s' from order not defined! We have %s" % (seq, taskProducers)
			sortedTaskProducers.extend(taskProducers[seq])
	for seq in taskProducers:
		if not "order" in rawTask or not seq in rawTask["order"]:
			sortedTaskProducers.extend(taskProducers[seq])
	result += "process.seq%s = cms.Sequence(%s)\n" % (name, " * ".join([ "cms.ignore(process.%s)" % prod for prod in sortedTaskProducers]))
	return (result, taskProducers)

def checkMissingProducts(attributes, task, products):
	result = {}
	productMissing = False
	for attribute in attributes:
		if "<taskname>" in attributes[attribute]:
			result[attribute] = attributes[attribute].replace("<taskname>", task)
			productName = result[attribute]
			for delimiter in ["'", '"']:
				if delimiter in productName:
					productName = productName.split(delimiter)[1]
			productMissing = productMissing or not productName in products
			if not productName in products:
				print "product missing:", result[attribute],
		else:
			result[attribute] = attributes[attribute]
	return (result, productMissing)

def createGenericAnalyzer(name, path, module, attributes, task, job):
	''' create Generic as defined in .ini'''
	settings = MainConfig(job=job)
	repMap = {
			  "name":name,
			  "task":task,
			  "path":path,
			  "module":module,
			  "MC":settings.monteCarloAvailable,
			  "attributes": "",
			  "expressions":"",
			  }
	for attribute in attributes:
		if not attribute in ["type", "path", "module"]:
			if "." in attribute:
				repMap["expressions"] += "process.%(task)s%(name)s." % repMap
				repMap["expressions"] += "%s = %s\n" % (attribute, attributes[attribute] % repMap)
			else:
				repMap["attributes"] += "%s = %s,\n" % (attribute, attributes[attribute] % repMap)


	result = """
from %(path)s import %(module)s
process.%(task)s%(name)s = %(module)s.clone(	
%(attributes)s
)
%(expressions)s
""" % repMap
	return result


def createDiLeptonAnalyzer(name, attributes, task, weightDefault, job):
	''' create DiLeptonAnalyzer as defined in .ini'''
	settings = MainConfig(job=job)
	repMap = {
			  "name":name,
			  "MC":settings.monteCarloAvailable,
			  "task":task,
			  "CSA_weighted": weightDefault
			  }
	repMap.update(attributes)

	return """
process.%(task)s%(name)s = DiLeptonAnalysis.clone(	
debug = False,
mcInfo = %(MC)s,
CSA_weighted = %(CSA_weighted)s,
	
mcSource = "%(mcSource)s",
electronSource = "%(electronSource)s",
muonSource = "%(muonSource)s",
tauSource = "%(tauSource)s",
metSource = "%(metSource)s",
jetSource = "%(jetSource)s"
)
""" % repMap


def getPATPset(flag, job, n, tasks, HLT, MVA=False):
	'''get PAT cfg file contents for SUSYDiLepton Analysis'''
	settings = MainConfig(job=job)
	#general stuff
	repMap = {
		"flag": flag,
		"taskName":settings.getTaskName(tasks),
		"job":job,
		"n":n,
		"HLT":HLT,
		"analyzers":"",
		"producerPath":"",
		"tasks":"",
		"additionalProducers":"",
		"globalTag":"",
		"counters":""
	 }
	#small helpers
	repMap["MessageLogger"] = MessageLogger("%(flag)s_%(taskName)s_%(job)s" % repMap)
	repMap["fileService"] = TFileService("%(flag)s_%(taskName)s_%(job)s.root" % repMap)
	repMap["OutputModule"] = getOutputModule("%(flag)s_%(taskName)s_%(job)s_EDM.root" % repMap, tasks[0])
	#print settings.getMap()["masterConfig"].get(job, "globalTag")
	#print "test"
	if "globalTag" in settings.getMap(): repMap["globalTag"] = """
process.load("Configuration.Geometry.GeometryIdeal_cff")
#process.load("Configuration.StandardSequences.Geometry_cff")
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
#from Configuration.PyReleaseValidation.autoCond import autoCond
process.GlobalTag.globaltag = cms.string(%(globalTag)s)
process.load("Configuration.StandardSequences.MagneticField_cff")
	""" % settings.getMap()
	#inputTags
	#repMap.update(settings.getInputTags(repMap["job"]))
	#sources
	#FIXME: deprecated for multicrab
	#if Grid:
	#	repMap["source"] = poolSourceGrid(job, n)
	#else:
	repMap["source"] = poolSourceLocal(job, n)
	#filters
	repMap["filters"] = ""
	if MVA:
		repMap["filters"] += createMVAFilter(repMap["taskName"])
		repMap["producerPath"] = "process.FourJetCut*process.DiLeptonCut*process.filter" + repMap["producerPath"]
	if HLT:
		repMap["filters"] += createHLTFilter(repMap["HLT"])
		repMap["producerPath"] = "process.LeptonHLT+" + repMap["producerPath"]
	#bJets
	repMap["bJetAlgo"] = "jetProbabilityJetTags"
	if settings.CSA == 'CSA07':
		repMap["bJetAlgo"] = "jetProbabilityJetTags"
	if settings.CSA == 'CSA08' or settings.CSA == 'Summer08':
		repMap["bJetAlgo"] = "jetProbabilityBJetTags"

	for name in settings.additionalProducers:
		repMap["additionalProducers"] += "from SuSyAachen.Skimming.defaults.%(name)s_cff import %(name)s\n" % {"name":name}
		repMap["additionalProducers"] += "%(name)s(process)\n" % {"name":name}
		if not repMap["producerPath"] == "": repMap["producerPath"] += "+ "
		repMap["producerPath"] += "process.seq%s " % name
	#load tasks
	products = []
	for task in tasks:
		(taskPset, taskProducts) = createTask(task, job)
		repMap["tasks"] += taskPset
		for cutFlowProducts in taskProducts.values():
			products.extend(cutFlowProducts)
		if not repMap["producerPath"] == "": repMap["producerPath"] += "+ "
		repMap["producerPath"] += "process.seq%s " % task
		if settings.makeCountHistos:repMap["counters"] += __createCounters(task, taskProducts)

	taskPaths = []
	
	for task in tasks:
		(thisAnalyzers, thisPaths) = __createAnalyzersAndPaths(task, products, job)
		repMap["analyzers"] += thisAnalyzers
		taskPaths.extend(thisPaths)
		if settings.makeCountHistos: repMap["counters"] += "process.%sCounters.count.append( cms.PSet(name = cms.string('analysis paths'), triggerNames = cms.vstring('%s') ) )\n" % (task, "', '".join([ i[8 + len(task) + 4:] for i in thisPaths]))

	if settings.makeCountHistos: repMap["counters"] += """
from SuSyAachen.Histograms.triggerResultsCounter_cfi import makeFilterPaths
process.counterPath = cms.EndPath( %s )
makeFilterPaths(process)
""" % (" + ".join(["process.%sCounters" % i for i in tasks]))

	repMap["taskPaths"] = ", ".join(taskPaths)

	if "process.outpath" in repMap["OutputModule"]:
		repMap["taskPaths"] += ", process.outpath"
		
	repMap["metUncertaintyTool"] = ""
	if settings.monteCarloAvailable and settings.makeMETUncertainties:
		repMap["producerPath"] = repMap["producerPath"] + " + process.metUncertaintySequence"	
		repMap["task"] = task
		repMap["metUncertaintyTool"] = """from PhysicsTools.PatUtils.tools.metUncertaintyTools import runMEtUncertainties
runMEtUncertainties(process,jetCollection="selectedPatJetsAK5PF",electronCollection="%sIsoElectrons",muonCollection="%sIsoMuons",dRjetCleaning=0.4,tauCollection=None,addToPatDefaultSequence=False)""" % (task,task)
			
	txt = """import FWCore.ParameterSet.Config as cms


process = cms.Process('Analysis')
process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")




%(MessageLogger)s
%(source)s

##--- GlobalTag
%(globalTag)s


########## Additional Producers ########################
%(additionalProducers)s

########## Filters ########################
%(filters)s

%(tasks)s

%(metUncertaintyTool)s


########## DiLeptonAnalyzers ##############
from SuSyAachen.DiLeptonHistograms.DiLeptonHistograms_cfi import DiLeptonAnalysis
%(analyzers)s

########## Output ##############
%(fileService)s

%(OutputModule)s
########## Paths ##########################
process.producerPath = cms.Path(%(producerPath)s )
process.schedule = cms.Schedule( process.producerPath, %(taskPaths)s)

########## Counting Histograms (must be at the very end) ##############
%(counters)s
""" % repMap
	#print txt
	return txt

def __makeFilters(rawFilters, task):
	result = []
	for rawName in rawFilters:
		prefix = ""
		name = rawName
		if name.startswith("!"):
			prefix = "~"
			name = name[1:]
		if not rawName == "":
			result.append("%sprocess.%s%s" % (prefix, task, name))
	return result

def __createAnalyzersAndPaths(task, products, job):
	settings = MainConfig(job=job)
	taskPaths = []
	analyzers = ""
	diLeptonAnalyzers = settings.getAnalyzers("DiLeptonAnalyzer")
	genericAnalyzers = settings.getAnalyzers("GenericAnalyzer")
	rawTask = settings.getRawTask(task, {"isMC": settings.monteCarloAvailable})

	modules = {"":[]}
	activeFilters = __makeFilters(rawTask["activeFilters"], task)
#	activeFilters = [ "process.%s%s" % (task, i) for i in rawTask["activeFilters"]]
	additionalFilters = {}
	if "additionalFilters" in rawTask:
		for name in rawTask["additionalFilters"]:
			additionalFilters[name] = __makeFilters(rawTask["additionalFilters"][name], task)
#			additionalFilters[name] = [ "process.%s%s" % (task, i) for i in rawTask["additionalFilters"][name]]
			modules[name] = []

	for analyzer in diLeptonAnalyzers:
		(attributes, productsMissing) = checkMissingProducts(diLeptonAnalyzers[analyzer], task, products)
		#productsMissing = False
		if not productsMissing:
			for name in modules:
				analyzers += createDiLeptonAnalyzer(name + analyzer, attributes, task,
								    (not settings.masterConfig.has_option(job, 'crosssection')) or float(settings.masterConfig.get(job, 'crosssection')) == 0, job)
				modules[name].append("process.%(task)s%(name)s%(analyzer)s" % {"task":task, "analyzer":analyzer, "name":name})

	for analyzer in genericAnalyzers:
		(attributes, productsMissing) = checkMissingProducts(genericAnalyzers[analyzer], task, products)
		#productsMissing = False
		if not productsMissing:
			
			for name in modules:
				if not "module" in genericAnalyzers[analyzer] or not "path" in genericAnalyzers[analyzer]:
					raise StandardError, "either 'module' or 'path' missing to create %s" % analyzer
				analyzers += createGenericAnalyzer(name + analyzer, genericAnalyzers[analyzer]["path"],
								   genericAnalyzers[analyzer]["module"],
								   attributes, task, job)
				modules[name].append("process.%(task)s%(name)s%(analyzer)s" % {"task":task, "analyzer":analyzer, "name":name})

	

	pathElements = []
	pathElements.extend(activeFilters)
	pathElements.extend(modules[""])
	#TODO sort analyzers bei optimal option here!
	analyzers += "process.%sPath =cms.Path(%s)\n" % (task, " * ".join(pathElements))
	taskPaths.append("process.%sPath" % task)
	for name in  additionalFilters:
		pathElements = []
		pathElements.extend(activeFilters)
		pathElements.extend(additionalFilters[name])
		pathElements.extend(modules[name])
		analyzers += "process.%sPath%s =cms.Path(%s)\n" % (task, name, " * ".join(pathElements))
		taskPaths.append("process.%sPath%s" % (task, name))
	return (analyzers, taskPaths)

def numbers(job):
	settings = MainConfig(job=job)
	originPath = os.path.abspath(os.path.curdir)
	os.chdir(settings.logpath + '/' + job)
	files = os.listdir('.')
	totalnumber = 0
	passednumber = 0
	print job + ':'
	if not dbsop.getDBSentry(job):
		for file in files:
			number = getNumberLog(file)
			if os.path.exists(settings.localdatapath + '/' + job + '/' + settings.filename + number + '.root') or os.path.exists(settings.datapath + '/' + job + '/' + settings.filename + number + '.root'):
				var1, var2 = search(file)
				if var2 == 1:
					print file
				if var1 == 0 and var2 == 0:
					print file
					srmop.srmdel(settings.datapath + '/' + job + '/' + settings.filename + number + '.root')
				totalnumber += var1
				passednumber += var2
	if dbsop.getDBSentry(job):
		 for file in files:
			var1, var2 = search(file)
                        totalnumber += var1
                        passednumber += var2
	os.chdir(originPath)
	return totalnumber, passednumber

