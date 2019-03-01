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
                def getVariables(expr):
                        import re
                        result = re.findall(r"(?![0-9])(\w+)", expr) # this is supposed to match all words = variable names that are not numbers. Words can end with numbers, though
                        result = [r for r in result if not r in ["and", "or"]] # remove and and or
                        return result
                # find variables used in cutstring (instead of looping through all branches)
                branchList = getVariables(expression)
                expression = expression.replace("&&","and")
                expression = expression.replace("&","and")
                expression = expression.replace("||","or")
                expression = expression.replace("|","or")

                evalGlobal = {"abs":fabs}
                for i in branchList:
                #for i in [i.GetName() for i in event.GetListOfBranches()]:
                        evalGlobal[i] = getattr(event,i)
                return eval(expression, evalGlobal)

        def getExpression(self, object):
                return self.config.get(self.section,"%sExpression"%object)
        
        
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
                endOfLine = 10000
                processors = self.config.get(self.section,"%sProcessors"%object).split()
                filter = " and ".join(processors)
                if self.config.has_option(self.section,"%sFilter"%object):
                        filter = self.config.get(self.section,"%sFilter"%object)
                print "looping over %s tree"%object

                for ev in src:
                        if (endOfLine < 1):
                                pass
                                #break
                        endOfLine -= 1
                        processingResults = {}
                        
                        for processorName in processors:
                                processingResults[processorName] = allProcessors[processorName].processEvent(ev, object)
     
                        if filter == "" or eval(filter, processingResults):
                                self._processEvent(ev, object)

                self._writeEventList("%s/selected.eventList"%(self.listPath), self.keepEvents.keys())
                for rejectedObject, rejectedList in self.rejected.iteritems():
                        self._writeEventList("%s/rejected.%s.eventList"%(self.listPath, rejectedObject), rejectedList)
                                                        
        def _processEvent(self, ev, object):
                rejectedObject = None
                fingerPrint = (ev.runNr, ev.lumiSec, ev.eventNr)
                if not fingerPrint in self.keepEvents:
                        self.keepEvents[fingerPrint] = (object, ev.pt1+ev.pt2, ev.chargeProduct)
                        
                ### No longer necessary since we store each event once in the ntuples
                ### Was used previously when we were storing each dilepton pair
                ### Now we only want to keep the first one to prefer mumu > ee > emu primary datasets           
                #~ elif self.keepEvents[fingerPrint][1] < ev.pt1+ev.pt2:
                        #~ rejectedObject = self.keepEvents[fingerPrint][0]
                        #~ self.keepEvents[fingerPrint] = (object, ev.pt1+ev.pt2, ev.chargeProduct) 
                                
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
                #~ print self.keepEvents
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

                        if not trees == None:
                                outDir = None
                                srcTree = {} 
                                for object in trees:
                                        srcTree[object] = TChain("%s%s"%(object, treeName))
                                        processors = self.config.get(section,"%sProcessors"%object).split()
                                        filter = " and ".join(processors)
                                        if self.config.has_option(section,"%sFilter"%object):
                                                filter = self.config.get(section,"%sFilter"%object)
                                        
                                        ### Quick and dirty workaround to prefer certain primary datasets (double muon > double electron > emu)
                                        ### To be in synch with ETH group
                                        ### Remove duplication of loops and conditions on path if this is to be removed again   
                                        
                                        for treePath in trees[object]:
                                                ### Use events from dimuon primary dataset first
                                                if not "DoubleMuon" in treePath:
                                                        continue
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

                                                else:
                                                        pass

                                                inFile.Close()
                                                srcTree[object].Add(treePath)
                                                print "adding", treePath
                                                                                
                                                                                        
                                        for treePath in trees[object]:
                                                ### Then take ee primary dataset 
                                                if not "DoubleElectron" in treePath:
                                                        continue
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

                                                else:
                                                        pass

                                                inFile.Close()
                                                srcTree[object].Add(treePath)
                                                print "adding", treePath        
        
                                        
                                                
                                        for treePath in trees[object]:
                                                ### Now the rest, but avoid taking a tree twice
                                                if "DoubleElectron" in treePath or "DoubleMuon" in treePath:
                                                        continue
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

                                                else:
                                                        pass

                                                inFile.Close()
                                                srcTree[object].Add(treePath)
                                                print "adding", treePath
                                                
                                        srcTree[object].SetBranchStatus("*", 1)
                                        #srcTree[object].SetBranchStatus("*", 0)
                                        #srcTree[object].SetBranchStatus("pt1", 1)
                                        #srcTree[object].SetBranchStatus("pt2", 1)
                                        #srcTree[object].SetBranchStatus("p4", 1)
                                        #srcTree[object].SetBranchStatus("chargeProduct", 1)
                                        #srcTree[object].SetBranchStatus("eventNr", 1)
                                        #srcTree[object].SetBranchStatus("runNr", 1)
                                        #srcTree[object].SetBranchStatus("lumiSec", 1)
                                        
                                        
                                        
                                        for processorName in processors:
                                                if processorName == "vtxWeighter":
                                                        srcTree[object].SetBranchStatus("weight", 0)
                                                        
                                                #### old code   
                                                if (self.treeProcessors[processorName].__class__.__name__ == SimpleSelector.__name__ and not self.config.has_option(section,"%sFilter"%object)):
                                                        print "Requirements met, applying simple selection boosting =)"
                                                        expression = self.treeProcessors[processorName].getExpression(object)
                                                        print "Cutting tree down to: '%s'" % (expression)
                                                        srcTree[object] = srcTree[object].CopyTree(expression)
                                                ######
                                                                                        
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
                                                
                                                ### old code
                                                for processorName in processors:
                                                        processingResults[processorName] = self.treeProcessors[processorName].processEvent(srcTree[object], object)
                                                if filter == "" or eval(filter, processingResults):
                                                        destTree.Fill()
                                                ####
                                                
 
                                                
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
    
        

