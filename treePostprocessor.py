#!/usr/bin/env VERSIONER_PYTHON_PREFER_32_BIT=yes python
# -*- coding: utf-8 -*-
'''
Created on 26.05.2011

@author: heron
'''

class TreeProcessor:
	def __init__(self, config, name):
		self.config = config
		self.section = "treeProcessor:%s"%name
		self.nThEntry = 0
		self.nEntries = None
		
	def prepareSrc(self, tree, object, processors):
		self.nEntries = tree.GetEntries()
		#print "%s: %d" % (self.section, self.nEntries)
		
	
	def prepareDest(self, tree, object):
		pass

	def processEvent(self, event, object):
		import sys
		self.nThEntry +=1
		#if self.nThEntry%(self.nEntries*0.001) < 1:
			#print "%d / %d" % (self.nThEntry, self.nEntries)
			#sys.stdout.write("\r%.1f%%" %(self.nThEntry*1./(self.nEntries*0.01)))    
			#sys.stdout.flush()  
		return True
	
class SimpleSelector(TreeProcessor):
	def __init__(self, config, name):
		TreeProcessor.__init__(self, config, name)
		
	def processEvent(self, event, object):
		from math import fabs
		expression = self.getExpression(object)
		expression = expression.replace("&&","and")
		expression = expression.replace("&","and")
		expression = expression.replace("||","or")
		expression = expression.replace("|","or")        
		evalGlobal = {"abs":fabs}
		for i in [i.GetName() for i in event.GetListOfBranches()]:
			evalGlobal[i] = getattr(event,i)
		return eval(expression, evalGlobal)

	def getExpression(self, object):
		return self.config.get(self.section,"%sExpression"%object)
		
		
class EventFilter(TreeProcessor):
	def __init__(self, config, name):
		TreeProcessor.__init__(self, config, name)
		
		names = self.config.get(self.section,"names").split(" ")
		self.eventList = readEventLists(names)
		
	def processEvent(self, event,object):
		result = True
		if event.runNr in self.eventList:
			if event.lumiSec in self.eventList[event.runNr]:
				if event.eventNr in self.eventList[event.runNr][event.lumiSec]:
					result = False
 
		return result
		
	
class SimpleWeighter(TreeProcessor):
	def __init__(self, config, name):
		TreeProcessor.__init__(self, config, name)
		self.weight = {}
		
	def prepareSrc(self, src, object, processors):
		#src.SetBranchStatus("weight", 0)
		pass
		
	def prepareDest(self, dest, object):
		from array import array
		self.weight[object] = array("f",[1.0])
		dest.Branch("weight2",self.weight[object],"weight2/F")

	def processEvent(self, event, object):
		self.weight[object][0] = event.weight*(event.pt1+event.pt2)
		return True
	
class VertexWeighter(TreeProcessor):
	def __init__(self, config, name):
		TreeProcessor.__init__(self, config, name)
		self.weight = {}
		
	def prepareSrc(self, src, object, processors):
		#src.SetBranchStatus("weight", 0)
		pass
		
	def prepareDest(self, dest, object):
		from array import array
		pass
		self.weight[object] = array("f",[1.0])
		dest.Branch("weight",self.weight[object],"weight/F")

	def processEvent(self, event, object):
		from helpers import getVtxWeight
		self.weight[object][0] = getVtxWeight(event.nVertices)
		return True

class NoFakeWeighter(TreeProcessor):
	def __init__(self, config, name):
		TreeProcessor.__init__(self, config, name)
		self.bName = config.get(self.section, "branchName")
		self.noFakeValue = eval(config.get(self.section, "weight"))
		self.weight = {} 
		
		
	#def prepareSrc(self, src, object, allProcessors):
	#    TreeProcessor.prepareSrc(self, src, object, allProcessors)
		#src.SetBranchStatus("weight", 0)
	#    pass
		
	def prepareDest(self, dest, object):
		from array import array
		TreeProcessor.prepareDest(self, dest, object)
		self.weight[object] = array("f",[self.noFakeValue])
		dest.Branch(self.bName,self.weight[object],"%s/F"%self.bName)
		
	#def processEvent(self, event, object):
	#    TreeProcessor.processEvent(self, event, object)
	#    return True


class FakeWeighter(TreeProcessor):
	def __init__(self, config, name):
		from helpers import parsePSet
		TreeProcessor.__init__(self, config, name)
		frPath = config.get(self.section, "fakePSet")
		self.branchName = config.get(self.section, "branchName")
		self.pSet = parsePSet(frPath)
		self.ptMax = 74.9
		self.weight = {}
		
	def prepareSrc(self, src, object, allProcessors):
		TreeProcessor.prepareSrc(self, src, object, allProcessors)
		#src.SetBranchStatus("weight", 0)
		pass
		
	def prepareDest(self, dest, object):
		from array import array
		TreeProcessor.prepareDest(self, dest, object)
		self.weight[object] = array("f",[-1.0])
		dest.Branch(self.branchName, self.weight[object],"%s/F"%self.branchName)
		
	def processEvent(self, event, object):
		TreeProcessor.processEvent(self, event, object)
		frBins = {}
		for (binName, varName) in zip(self.config.get(self.section,"binNames").split(),self.config.get(self.section,"varNames").split()):
			frBins[binName] = getattr(event,varName)
		for binName in frBins:
			if "pt" in binName and frBins[binName] > self.ptMax:
				frBins[binName] = self.ptMax
		idExpr = self.config.get(self.section,"idExpr")
		evalGlobals = {"id1":event.id1,
					   "id2":event.id2}
		self.weight[object][0] = -1
		if eval(idExpr,evalGlobals):
			frType = "center"
			frType = self.config.get(self.section,"frType")
			f = self.pSet[frType].fakeRate(frBins)
			self.weight[object][0] = f/(1-f)
		return True

	
class OverlapRemover(TreeProcessor):
	def __init__(self, config, name):
		from os.path import exists as pathExists
		from os import makedirs
		TreeProcessor.__init__(self, config, name)
		self.keepEvents = {}
		self.rejected = {}
		self.listPath = self.config.get(self.section,"listPath")
		if not pathExists(self.listPath):
			makedirs(self.listPath)
	
	def prepareSrc(self, src, object, allProcessors):
		TreeProcessor.prepareSrc(self, src, object, allProcessors)
		endOfLine = 1000
		for ev in src:
			if (endOfLine < 1):
				pass
				#continue
			endOfLine -= 1
			processingResults = {}
			processors = self.config.get(self.section,"%sProcessors"%object).split()
			filter = " and ".join(processors)
			if self.config.has_option(self.section,"%sFilter"%object):
				filter = self.config.get(self.section,"%sFilter"%object)
			for processorName in processors:
				processingResults[processorName] = allProcessors[processorName].processEvent(ev, object)
			# debugging
			#if (ev.lumiSec == 131):
			#    print "event %d: %s" % (ev.eventNr, processingResults)
				
			if filter == "" or eval(filter, processingResults):
				self._processEvent(ev, object)
		self._writeEventList("%s/selected.eventList"%(self.listPath), self.keepEvents.keys())
		for rejectedObject, rejectedList in self.rejected.iteritems():
			self._writeEventList("%s/rejected.%s.eventList"%(self.listPath, rejectedObject), rejectedList)
							
	def _processEvent(self, ev, object):
		rejectedObject = None
		fingerPrint = (ev.runNr, ev.lumiSec, ev.eventNr) 
		if not fingerPrint in self.keepEvents:
			self.keepEvents[fingerPrint] = (object, ev.pt1+ev.pt2)
		elif self.keepEvents[fingerPrint][1] < ev.pt1+ev.pt2 or ("Tau" in self.keepEvents[fingerPrint][0] and not "Tau" in object):
			rejectedObject = self.keepEvents[fingerPrint][0]
			self.keepEvents[fingerPrint] = (object, ev.pt1+ev.pt2)                
		else:
			rejectedObject = object
		if rejectedObject:
			if not rejectedObject in self.rejected:
				self.rejected[rejectedObject] = []
			self.rejected[rejectedObject].append(fingerPrint)     
			
	def _writeEventList(self, path, list):
			file = open(path,"w")
			file.write("\n".join([":".join(["%s"%j for j in i]) for i in list]))
			file.close()
	
	def processEvent(self, event, object):
		TreeProcessor.processEvent(self, event, object)
		fingerPrint = (event.runNr, event.lumiSec, event.eventNr)        
		#if fingerPrint in self.keepEvents and not object == self.keepEvents[fingerPrint][0]:
		#    print "skipping", fingerPrint, object, event.pt1+event.pt2,   self.keepEvents[fingerPrint]
		value = fingerPrint in self.keepEvents and object == self.keepEvents[fingerPrint][0]
		value2 = True
		if (value):
			# checks if correct sumPt is matched
			# necessary for same-flavour events
			value2 = event.pt1+event.pt2 == self.keepEvents[fingerPrint][1]

		# remove this event from the keepEvents list
		# -> remove duplicates
		if (value and value2):
			self.keepEvents.pop(fingerPrint)
			
		return (value and value2)

class TreeProducer:
	def __init__(self, config, inputPaths, name = None):
		from os.path import split as splitPath
		from os.path import exists as pathExists
		from os import makedirs
		from sys import modules
		if name == None:
			assert len(inputPaths) == 1, "can only determine names for singlePaths automatically. Got '%s'"%inputPaths
			name = splitPath(inputPaths[0])[1].split(".")[2]
		self.config = config
		self.name = name
		self.tasks = list(set([splitPath(i)[1].split(".")[1] for i in inputPaths]))
		self.flags = list(set([splitPath(i)[1].split(".")[0] for i in inputPaths]))
		self.inputPaths = inputPaths
		self.counterSum = None
		self.outPath = config.get("general","outPath")
		if not pathExists(self.outPath):
			makedirs(self.outPath)
		self.treeProcessors = {}
		for section in self.config.sections():
			if section.startswith("treeProcessor:"):
				processorName = section.split("treeProcessor:")[1]
				processorType = self.config.get(section,"type")
				#warning black magic ahead :P
				self.treeProcessors[processorName] = getattr(modules[globals()["__name__"]],processorType)(self.config, processorName)
		
	def produce(self):
		from ROOT import TFile, TChain, TH1
		from os.path import exists as pathExists
		from os.path import split as splitPath
		outFilePath = "%s/%s.%s.%s.root"%(self.outPath, "".join(self.flags), "processed" , self.name)
		#if pathExists(outFilePath):
		#    return
		outFile = TFile("%s/%s.%s.%s.root"%(self.outPath, "".join(self.flags), "processed" , self.name),"recreate")
		for section in self.config.sections():            
			trees = None
			if section.startswith("dileptonTree:"):
				treeProducerName =self.config.get(section,"treeProducerName")
				trees = self._getDileptonTrees(section)
				treeName = "DileptonTree"
				subDirName = "%s%s"%(section.split("dileptonTree:")[1],treeProducerName)
			if section.startswith("isoTree:"):
				treeProducerName =self.config.get(section,"treeProducerName")
				trees = self._getIsoTrees(section)
				treeName = "Iso"
				subDirName = "%s%s"%(section.split("isoTree:")[1],treeProducerName)
			if not trees == None:
				outDir = None
				srcTree = {} 
				for object in trees:
			
					srcTree[object] = TChain("%s%s"%(object, treeName))
					processors = self.config.get(section,"%sProcessors"%object).split()
					filter = " and ".join(processors)
					if self.config.has_option(section,"%sFilter"%object):
						filter = self.config.get(section,"%sFilter"%object)
					for treePath in trees[object]:
						#srcFile = TFile(filePath,"r")
						#srcTree = srcFile.Get(treePath)
						filePath = "%s.root"%treePath.split(".root")[0]
						inFile = TFile(filePath,"READ")
						makeCounterSum = eval(self.config.get("general","counterSum"))
						print "Add counter sum: %s" % makeCounterSum
						if not self.counterSum and makeCounterSum:
							if not outFile.GetDirectory("%sCounters" % section.split("dileptonTree:")[1]):
								outFile.mkdir("%sCounters" % section.split("dileptonTree:")[1])
							outFile.cd("%sCounters" % section.split("dileptonTree:")[1])
							task = None 
							
							if "vtxWeighter" in processors:  
								t =  self.config.get("general","tasks")
								
								if ".%s."%t in splitPath(filePath)[1]:
									assert task == None, "unable to disambiguate tasks '%s' matches both '%s' and '%s'"(filePath, task, t)
									task = t
								else:
									task = t
							else:                         
								for t in self.tasks:
									if ".%s."%t in splitPath(filePath)[1]:
										assert task == None, "unable to disambiguate tasks '%s' matches both '%s' and '%s'"(filePath, task, t)
										task = t
							self.counterSum = inFile.Get("%sCounters/analysis paths"%task).Clone()

							## also add 3D weights
							#outFile.mkdir("%sWeightSummer" % section.split("dileptonTree:")[1])
							#outFile.cd("%sWeightSummer" % section.split("dileptonTree:")[1])
							## task has been defined above
							#self.weightSum = inFile.Get("%sWeightSummer/Weights"%task).Clone()
						else:
							pass
							#need to cope with different lumis :( 
							#h = inFile.Get("%sCounters/analysis paths"%task)
							#print inFile, "%sCounters/analysis paths"%task, h
							#self.counterSum.Add( h,1. )
						inFile.Close()
						srcTree[object].Add(treePath)
						print "adding", treePath
					srcTree[object].SetBranchStatus("*", 1)
					
					if (self.treeProcessors[filter].__class__.__name__ == SimpleSelector.__name__ and self.config.has_option(section,"%sFilter"%object)):
						expression = self.treeProcessors[filter].getExpression(object)
						print "Cutting tree down to: '%s'" % (expression)
						outFile.Write()
						outFile.Close()
						srcTree[object] = srcTree[object].CopyTree(expression)					
						outFile = TFile("%s/%s.%s.%s.root"%(self.outPath, "".join(self.flags), "processed" , self.name),"UPDATE")
	
					for processorName in processors:
						if processorName == "vtxWeighter":
							srcTree[object].SetBranchStatus("weight", 0)
						self.treeProcessors[processorName].prepareSrc(srcTree[object], object, self.treeProcessors)
				for object in trees:
					processors = self.config.get(section,"%sProcessors"%object).split()
					filter = " and ".join(processors)
					if self.config.has_option(section,"%sFilter"%object):
						filter = self.config.get(section,"%sFilter"%object)
					
					if not outDir:
						outDir = outFile.mkdir(subDirName)
					outFile.cd(subDirName)
 
					destTree = srcTree[object].CloneTree(0)
					destTree.SetAutoSave(5000000000)
					#print processors
					for processorName in processors:
						self.treeProcessors[processorName].prepareDest(destTree, object)
						#~ print "%s: %d" % (str(processorName), self.treeProcessors[processorName].nEntries)
					endOfLine = 1000
					for i in srcTree[object]:
						if endOfLine < 1:
							pass
							#continue
						endOfLine -= 1
						processingResults = {}
						keep = False
						for processorName in processors:
							keep = self.treeProcessors[processorName].processEvent(srcTree[object], object)
						
						if keep:
							destTree.Fill()
					#srcFile.Close()
					outFile.Write()
				#from pprint import pprint
				#pprint( trees)

		outFile.Purge()
		outFile.Close()
				
				
	def _getIsoTrees(self, section):
		from re import match
		from os.path import split as splitPath
		result = {}
		datasetPaths = []
		treeProducerName =self.config.get(section,"treeProducerName")
		datasetExpression = self.config.get(section, "Dataset")
		datasetSelection = self.config.get(section, "Selection")
		for path in self.inputPaths:
			if not match(datasetExpression, splitPath(path)[1].split(".")[2]) == None:
				datasetPaths.append(path)
		if datasetPaths == []:
				datasetSelection = self.config.get(section, "otherSelection")
				datasetPaths = self.inputPaths
		result[""] = []
		for path in datasetPaths:
			task = None
			for t in self.tasks:
				if ".%s."%t in splitPath(path)[1]:
					assert task == None, "unable to disambiguate tasks '%s' matches both '%s' and '%s'"(path, task, t)
					task = t
			result[""].append( "%s/%s%s%s/Trees/Iso"%(path,task,datasetSelection,treeProducerName))
		return result
		
		
	def _getDileptonTrees(self, section):
		from re import match
		from os.path import split as splitPath
		result = {}
		objects = self.config.get(section,"objects").split()
		treeProducerName =self.config.get(section,"treeProducerName")
		for object in objects:
			processors = self.config.get(section,"%sProcessors"%object).split()
			datasetPaths = []
			datasetExpression = self.config.get(section, "%sDataset"%object)
			datasetSelection = self.config.get(section, "%sSelection"%object)
			for path in self.inputPaths:
				if not match(datasetExpression, splitPath(path)[1].split(".")[2]) == None:
					datasetPaths.append(path)
			if datasetPaths == []:
				datasetSelection = self.config.get(section, "otherSelection")
				datasetPaths = self.inputPaths
			
			result[object] = []
			for path in datasetPaths:
				task = None
				if "vtxWeighter" in processors:
					t =  self.config.get("general","tasks")
					if ".%s."%t in splitPath(path)[1]:
						assert task == None, "unable to disambiguate tasks '%s' matches both '%s' and '%s'"(path, task, t)
						task = t
					else:
						task = t
				else:					
					for t in self.tasks:
						if ".%s."%t in splitPath(path)[1]:
							assert task == None, "unable to disambiguate tasks '%s' matches both '%s' and '%s'"(path, task, t)
							task = t
				
				result[object].append( "%s/%s%s%s/%sDileptonTree"%(path,task,datasetSelection,treeProducerName,object))
		return result


def readEventLists(names):
	result = {}
	for name in names:
		lines = [line.rstrip('\n') for line in open(name)]
	for line in lines:
	  runNr = int(line.split(":")[0])
	  lumiSec = int(line.split(":")[1])
	  eventNr = int(line.split(":")[2])
	  if not runNr in result:
		result[runNr] = {}
	  
	  if not lumiSec in result[runNr]:
		 result[runNr][lumiSec] = []
	  result[runNr][lumiSec].append(eventNr)
	return result		
def getProducers(config, path):
	from glob import glob
	from re import match
	from os.path import split as splitPath
	mcExpression = config.get("general","MCDatasets")
	result = []
	dataPaths = []
	for inputPath in glob("%s/*.root"%path):
		if match(mcExpression, splitPath(inputPath)[1]) ==None:
			#~ print "TEST!!!"
			#~ print mcExpression
			#~ print splitPath(inputPath)[1]
			dataPaths.append(inputPath)
		else:   
			result.append(TreeProducer(config, [inputPath]))
	if len(dataPaths) > 0:
		result.append(TreeProducer(config, dataPaths, "MergedData"))
	return result

	
	
def main(argv = None):
	import sys
	from ConfigParser import ConfigParser
	from optparse import OptionParser
	
	sys.path.append('../frameWorkBase/')
	from helpers import getVtxWeight
	
	if argv == None:
		argv = sys.argv[1:]
	parser = OptionParser()
	parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
						  help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
	(opts, args) = parser.parse_args(argv)

	if opts.Config == []:
		opts.Config = [ "default.ini" ]
	
	config = ConfigParser()
	config.read(opts.Config)
	
	basePath = config.get("general","basePath")
	producers = getProducers(config, basePath)
	for p in producers:
		p.produce()
	
if __name__ == '__main__':
	main()

import unittest    

class plotTest(unittest.TestCase):
	configString ="""
[general]
tasks = pfBaseCuts pfBaseCutsSingleMu pfBaseCutsSingleE pfBaseCutsTauPlusX
basePath = /Users/heron/Documents/superSymmetry/results/diLeptonTaus/diLeptons41x/susy0447v5/input
MCDatasets = .*_Spring11
outPath = processedTrees

[dileptonTree NoCuts]
treeProducerName = TaNCTrees
objects = EE EMu MuMu ETau MuTau TauTau
EEDataset = SingleElectron.* 
EESelection = HLTE
EEProcessors = htSelector ptSumWeighter overlap
EEFilter = True
EMuDataset = SingleMu_.*
EMuSelection = HLTIsoMu
EMuProcessors = htSelector ptSumWeighter overlap
EMuFilter = htSelector 
MuMuDataset = SingleMu_.*
MuMuSelection = HLTMu
MuMuProcessors = htSelector overlap
ETauDataset = TauPlusX_.*
ETauSelection = HLTETau
ETauProcessors = htSelector overlap
MuTauDataset = TauPlusX_.*
MuTauSelection = HLTMuTau
MuTauProcessors = htSelector overlap
TauTauDataset = TauPlusX_.*
TauTauSelection = HLTTauTauHT
TauTauProcessors = htSelector overlap
OtherSelection =

[dileptonTree:NoCuts]
treeProducerName = TaNCTrees
objects = EE EMu MuMu ETau MuTau TauTau
EEDataset = SingleElectron.* 
EESelection = HLTE
EEProcessors = overlap
EMuDataset = SingleMu_.*
EMuSelection = HLTIsoMu
EMuProcessors = overlap 
MuMuDataset = SingleMu_.*
MuMuSelection = HLTMu
MuMuProcessors = overlap
ETauDataset = TauPlusX_.*
ETauSelection = HLTETau
ETauProcessors = overlap
MuTauDataset = TauPlusX_.*
MuTauSelection = HLTMuTau
MuTauProcessors = overlap
TauTauDataset = TauPlusX_.*
TauTauSelection = HLTTauTauHT
TauTauProcessors = overlap
OtherSelection = 
 

[isoTree NoCuts]
treeProducerName = TnPTaNCTauTrees
Dataset = TauPlusX
Selection = 
Processors = tauFakeWeights
PtherSelection = 

[treeProcessor:htSelector]
type = SimpleSelector

[treeProcessor:lowPtSelector]
type = SimpleSelector
EEExpression = pt1 > 20 && pt2 > 20 && ht > 250 
EMuExpression = pt1 > 20 && pt2 > 20 && ht > 250 
MuMuExpression = pt1 > 20 && pt2 > 20 && ht > 250 
ETauExpression = pt1 > 20 && pt2 > 15 && ht > 250 
MuTauExpression = pt1 > 20 && pt2 > 15 && ht > 250 
TauTauExpression = pt1 > 20 && pt2 > 15 && ht > 250 


[treeProcessor:ptSumWeighter]
type = SimpleWeighter

[treeProcessor:vtxWeighter]
type = VertexWeighter

[treeProcessor:tauFakeWeights]
type = FakeWeighter
fakePSet = /Users/heron/Documents/superSymmetry/results/diLeptonTaus/diLeptons41x/susy0447v5/tauDataHT_cff.py
selection = tauDiscr > 0.5

[treeProcessor:overlap]
type = OverlapRemover
listPath = eventLists
EEProcessors = lowPtSelector
EMuProcessors = lowPtSelector
MuMuProcessors = lowPtSelector
ETauProcessors = lowPtSelector
MuTauProcessors = lowPtSelector
TauTauProcessors = lowPtSelector

	"""
	
	def setUp(self):
		from ConfigParser import ConfigParser
		configFile = open("treePostprocessor.unittest.General.ini","w")
		configFile.write(self.configString)
		configFile.close()
		
		self.config = ConfigParser()
		self.config.read("treePostprocessor.unittest.General.ini")

	
	def tearDown(self):
		from os import remove
		try: remove("treePostprocessor.unittest.General.ini")
		except: pass    
	
	def testProducer(self):
		basePath = self.config.get("general","basePath")
		producers = getProducers(self.config, basePath)
		for p in producers:
			#print p.name, p.inputPaths
			if not p.name == "MergedData":                
				p.produce()

		#main(["unittest","-C","treePostprocessor.unittest.General.ini"])
		
		

