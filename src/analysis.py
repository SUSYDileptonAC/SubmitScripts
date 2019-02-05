# -*- coding: utf-8 -*-
import os, subprocess, re, glob

from src.mainConfig import MainConfig
      
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

def poolSourceLocal(job, n):
        settings = MainConfig(job=job)
#       txt = 'process.source = cms.Source(\'PoolSource\', \n'

    ##################Fixme: How to handle this on data
#       txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
#       txt += "eventsToProcess = cms.untracked.VEventRange('1:4165-1:4165'),\n"
#       txt += '     fileNames = cms.untracked.vstring('
        files = glob.glob("%(localdatapath)s/" % settings.getMap() + job + "/*.root")
        files = ["file:%s" % i for i in files]
        if settings.getMap()["masterConfig"].has_option(job, "localListPath"):
                localListPath = settings.getMap()["masterConfig"].get(job, "localListPath")
                listFile = open(localListPath, "r")
                files = ["dcap://grid-dcap.physik.rwth-aachen.de/pnfs/physik.rwth-aachen.de/cms/%s" % i for i in
                         listFile.read().split()]
                listFile.close()
        #       print "#####", settings.numCores, settings.coreNumber
        txt = "fileList = %s\n" % files

        if settings.verbose: print "running localy on %i files in '%s'" % (len(files), "%(localdatapath)s/" % settings.getMap() + job)
        #if settings.verbose == True: print "%(localdatapath)s/" % settings.getMap() + job + "/*.root"

        #txt += ",\n".join(["\t\t'%s'" % file for file in files])
        txt += 'process.source = cms.Source(\'PoolSource\', \n'

        ##################Fixme: How to handle this on data        

        
        #txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
        #txt += "     eventsToProcess = cms.untracked.VEventRange('1:65735500-1:65735500'),\n"
        txt += '     fileNames = cms.untracked.vstring(fileList),\n'
        txt += '     duplicateCheckMode = cms.untracked.string(\'noDuplicateCheck\'),\n'
        #for file in files:
        #       txt += '\'file:' + file + '\','
        #txt = txt[:-1] # remove the last comma
#       txt += ')\n'
        txt += ')\n\n'
        cmsswBlocks = settings.getMap()["crabAdditionsBlocks"]["Data-AdditionsBlock"].splitlines()
        jsonPath = None
        for cmsswBlock in cmsswBlocks:
                print cmsswBlock
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

def __createCounters(taskName, taskProducers):
        settings = MainConfig()
        result = """
from SuSyAachen.DiLeptonHistograms.triggerResultsCounter_cfi import triggerResultsCounter
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
                                                if type(producer[srcAttribute]) == type(""):
                                                        def replaceOnFlyProducer(matchobj):
                                                                onFlyProducerName = None
                                                                if len(matchobj.groups()) == 1 and matchobj.group(1) in rawTask:
                                                                        onFlyProducerName = rawTask[matchobj.group(1)][-1]["name"]
                                                                else:
                                                                        for onFlyProducer in rawTask[matchobj.group(1)]:
                                                                                if onFlyProducer["name"] == matchobj.group(2):
                                                                                        onFlyProducerName = matchobj.group(2)
                                                                return "%s%s" % (name, onFlyProducerName)
                                                        if "." in producer[srcAttribute]:
                                                                inputCollections[srcAttribute] = sub("\((.*?)\.(.*?)\)", replaceOnFlyProducer, producer[srcAttribute])
                                                        else:
                                                                inputCollections[srcAttribute] = sub("\((.*?)\)", replaceOnFlyProducer, producer[srcAttribute])
                                                else:
                                                        inputCollections[srcAttribute] = producer[srcAttribute]

                                if inputCollections == {}:
                                        raise StandardError, "could not find inputCollection(s) (%s) in '%s' of task '%s'" % (srcAttributes, sequence, name)

                                for srcAttribute in srcAttributes:
                                        producer[srcAttribute] = inputCollections[srcAttribute]

                                for attribute in producer:
                                        if not attribute in ["name", "selector", "skip", "srcNames"]:
                                                value = repr(producer[attribute])
                                                # If value is a string that starts with ?, replace with non-string (need to remove ? and ' ')
                                                if type(producer[attribute]) == type("") and producer[attribute].startswith("?"):
                                                        value = value[2:-1]
                                                repMap["attributes"] += "       %s = %s,\n" % (attribute, value)
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
                          "imports":"",
                          }
        
        if "imports" in attributes:
                imports = [imp.strip() for imp in attributes["imports"].split(",")]
        else:
                imports = []
                          
        for imp in imports:
                if not imp.endswith("_cfi"):
                        imp = "%s_cfi"%(imp)
                if "." in imp:
                        imp_insert = imp
                else:
                        imp_insert = "SuSyAachen.DiLeptonHistograms.%s"%(imp)
                repMap["imports"] += "from %s import *\n" % imp_insert
                
        
        for attribute in attributes:
                if not attribute in ["type", "path", "module", "imports"]:
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
        return result, repMap["imports"]


def getPATPset(flag, job, n, tasks, HLT):
        '''get PAT cfg file contents for SUSYDiLepton Analysis'''
        settings = MainConfig(job=job)
        #general stuff
        repMap = {
                "flag": flag,
                "taskName":settings.getTaskName(tasks),
                "job":job,
                "n":n,
                "HLT":HLT,
                "imports":"",
                "analyzers":"",
                "producerPath":"",
                "tasks":"",
                "additionalProducers":"",
                "globalTag":"",
                "counters":"",
         }
        #small helpers
        repMap["MessageLogger"] = MessageLogger("%(flag)s_%(taskName)s_%(job)s" % repMap)
        repMap["fileService"] = TFileService("%(flag)s_%(taskName)s_%(job)s.root" % repMap)
        repMap["OutputModule"] = getOutputModule("%(flag)s_%(taskName)s_%(job)s_EDM.root" % repMap, tasks[0])
        #print settings.getMap()["masterConfig"].get(job, "globalTag")
        #print "test"
        if "globalTag" in settings.getMap(): repMap["globalTag"] = """
#process.load("Configuration.Geometry.GeometryIdeal_cff")
process.load('Configuration.StandardSequences.GeometryDB_cff')
process.load("Configuration.StandardSequences.FrontierConditions_GlobalTag_cff")
#from Configuration.PyReleaseValidation.autoCond import autoCond
process.GlobalTag.globaltag = cms.string(%(globalTag)s)
process.load("Configuration.StandardSequences.MagneticField_cff")
        """ % settings.getMap()

        repMap["source"] = poolSourceLocal(job, n)
        #filters
        repMap["filters"] = ""
        if HLT:
                repMap["filters"] += createHLTFilter(repMap["HLT"])
                repMap["producerPath"] = "process.LeptonHLT+" + repMap["producerPath"]
        
        for name in settings.additionalProducers:
                if "|" in name:
                        fileName,suffix = name.split("|")
                else:
                        fileName,suffix = name,""
                        
                repMap["additionalProducers"] += "from SuSyAachen.Skimming.defaults.%(name)s_cff import %(name)s%(suffix)s\n" % {"name":fileName, "suffix":suffix}
                repMap["additionalProducers"] += "%(name)s%(suffix)s(process)\n" % {"name":fileName, "suffix":suffix}
                if not repMap["producerPath"] == "": repMap["producerPath"] += "+ "
                repMap["producerPath"] += "process.seq%s%s " % (fileName, suffix)
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
                (thisAnalyzers, thisPaths, imports) = __createAnalyzersAndPaths(task, products, job)
                #print thisAnalyzers, thisPaths, task
                repMap["analyzers"] += thisAnalyzers
                repMap["imports"] += imports
                taskPaths.extend(thisPaths)
                if settings.makeCountHistos: repMap["counters"] += "process.%sCounters.count.append( cms.PSet(name = cms.string('analysis paths'), triggerNames = cms.vstring('%s') ) )\n" % (task, "', '".join([ i[8 + len(task) + 4:] for i in thisPaths]))

        if settings.makeCountHistos: repMap["counters"] += """
from SuSyAachen.DiLeptonHistograms.triggerResultsCounter_cfi import makeFilterPaths
process.counterPath = cms.EndPath( %s )
makeFilterPaths(process)
""" % (" + ".join(["process.%sCounters" % i for i in tasks]))

        repMap["taskPaths"] = ", ".join(taskPaths)

        if "process.outpath" in repMap["OutputModule"]:
                repMap["taskPaths"] += ", process.outpath"
                
        if int(settings.CSA.split("X")[0]) >= 92:
                repMap["makeUnscheduled"] = """
#--- Add everything to Tasks so that unscheduled execution is possible
from FWCore.ParameterSet.Utilities import convertToUnscheduled
process=convertToUnscheduled(process)
from FWCore.ParameterSet.Utilities import cleanUnscheduled
process=cleanUnscheduled(process)"""
        else:
                repMap["makeUnscheduled"] = ""
                          
        txt = """import FWCore.ParameterSet.Config as cms


process = cms.Process('Analysis')

process.load("SimGeneral.HepPDTESSource.pythiapdt_cfi")




%(MessageLogger)s
%(source)s

##--- GlobalTag
%(globalTag)s

## Imports needed for Filters and Analyzer

%(imports)s

process.options.allowUnscheduled = cms.untracked.bool(True) # still needed for 80X, obsolete from 91X on

########## Additional Producers ########################
%(additionalProducers)s


########## Filters ########################
%(filters)s

%(tasks)s

########## DiLeptonAnalyzers ##############
%(analyzers)s


########## Output ##############
%(fileService)s

%(OutputModule)s
########## Paths ##########################
process.producerPath = cms.Path(%(producerPath)s )
process.schedule = cms.Schedule( process.producerPath, %(taskPaths)s)


########## Counting Histograms (must be at the very end) ##############
%(counters)s

%(makeUnscheduled)s

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
        genericAnalyzers = settings.getAnalyzers("GenericAnalyzer")
        rawTask = settings.getRawTask(task, {"isMC": settings.monteCarloAvailable})

        modules = {"":[]}
        activeFilters = __makeFilters(rawTask["activeFilters"], task)
        additionalFilters = {}
        if "additionalFilters" in rawTask:
                for name in rawTask["additionalFilters"]:
                        additionalFilters[name] = __makeFilters(rawTask["additionalFilters"][name], task)
                        modules[name] = []

        
        imports = ""
        for analyzer in genericAnalyzers:
                (attributes, productsMissing) = checkMissingProducts(genericAnalyzers[analyzer], task, products)
                #productsMissing = False
                if not productsMissing:
                        
                        for name in modules:
                                if not "module" in genericAnalyzers[analyzer] or not "path" in genericAnalyzers[analyzer]:
                                        raise StandardError, "either 'module' or 'path' missing to create %s" % analyzer
                                newAnalyzer, newImports = createGenericAnalyzer(name + analyzer, genericAnalyzers[analyzer]["path"],
                                                                   genericAnalyzers[analyzer]["module"],
                                                                   attributes, task, job)
                                analyzers += newAnalyzer
                                imports += newImports
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
        return (analyzers, taskPaths, imports)
