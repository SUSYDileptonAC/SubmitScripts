'''
Created on 23.06.2009

@author: edelhoff
@edited: mohr
'''

import ConfigParser
import os.path
import re

import __main__

class BetterConfigParser(ConfigParser.ConfigParser):

    def get(self, section, option):
        result = ConfigParser.ConfigParser.get(self, section, option, raw=True)
        result = self.__replaceSectionwideTemplates(result)
        return result

    def optionxform(self, optionstr):
        '''
        enable case sensitive options in .ini files
        '''
        return optionstr

    def __replaceSectionwideTemplates(self, data):
        '''
        replace <section|option> with get(section,option) recursivly
        '''
        result = data
        findExpression = re.compile("((.*)\<(.*)\|(.*)\>(.*))*")
        groups = findExpression.search(data).groups()
        if not groups == (None, None, None, None, None): # expression not matched
            result = self.__replaceSectionwideTemplates(groups[1])
            result += self.get(groups[2], groups[3])
            result += self.__replaceSectionwideTemplates(groups[4])
        return result

class MainConfig:
    '''
    Main configuration for all the SubmitScripts options
    a bit ugly singleton construction via __main__ :/
    '''

    def __init__(self, configPaths=None, options=None, job=None):
        self.theGlobalName = "__theMainConfigMap__"
        if configPaths == None:
            if not job == None:
                self.getMap()[ "monteCarloAvailable" ] &= not "Data" in self.getMap()[ "masterConfig"].get(job, 'groups')
            if not self.__testSetUp():
                raise StandardError, "MainConfiguration has not been set up!"
        elif self.__testSetUp():
            raise StandardError, "MainConfiguration already been set up!"
        else:
            config = BetterConfigParser()

            config.read(self.__cleanPaths(configPaths))
            CSA = config.get('general', 'CSA')

            __main__.__dict__[ self.theGlobalName ] = {
                #-- general options
                "numCores":6,
                "CSA": CSA,
                "email": os.path.expandvars(config.get("general", 'email')),
                "groups": config.get("general", 'groups').split(),
                "InputTagCollection": config.get("general", "InputTagCollection"),
                "nSkimEvents": config.get("general" , "nSkimEvents"),
                "minFileSize": config.get("general" , "minFileSize"),
                "StatusPath": config.get("general" , "StatusPath"),
                #-- crab options
		        #~ "CrabServer": config.get("crab", 'CrabServer'),
                "StageoutSite": config.get("crab", 'StageoutSite'),
                "nEventsPerJob": config.get("crab", 'nEventsPerJob'),
                #~ "user_remote_dir": os.path.expandvars(config.get("crab", 'user_remote_dir')),
		"lumis_per_job": os.path.expandvars(config.get("crab", 'lumis_per_job')),		
		"publish": os.path.expandvars(config.get("crab", 'publish')),		
		"pubDBSURL": os.path.expandvars(config.get("crab", 'pubDBSURL')),		
				
                #--CSA specific options
                "monteCarloAvailable": eval(config.get(CSA, 'monteCarloAvailable')), #must be True or False
                "makeMETUncertainties": eval(config.get(CSA, 'makeMETUncertainties')), #must be True or False		
                "skimpath": self.__formatPath(config.get(CSA, 'skimpath')),
                "skimFromLocalDBS": "True" in config.get(CSA, "skimFromLocalDBS"),
                "logpath":  self.__formatPath(config.get(CSA, 'skimlogpath')),
                "datapath":  config.get(CSA, 'datapath'),
                "localdatapath":  self.__formatPath(config.get(CSA, 'localdatapath')),
                "analysispath":  self.__formatPath(config.get(CSA, 'analysispath')),
                "localhistopath":  self.__formatPath(config.get(CSA, 'localhistopath')),
                "mergedhistopath": self.__formatPath(config.get(CSA, 'mergedhistopath')),
                "tasksPath":  [self.__formatPath(i) for i in config.get(CSA, 'tasksPath').split()],
                "analogpath":  self.__formatPath(config.get(CSA, 'analogpath')),
                "storagepath":  self.__formatPath(config.get(CSA, 'storagepath')),
                "histogramstoragepath":  self.__formatPath(config.get(CSA, 'histogramstoragepath')),
                "cmsstoragepath":  config.get(CSA, 'cmsstoragepath'),
                "filename":  config.get(CSA, 'filename'),
                "logname":  config.get(CSA, 'logname'),
                #in skimpath
                "skimcfgname":  config.get(CSA, 'skimcfgname'),
                # output of skimcfgname
                "skimoutputfiles":  config.get(CSA, 'skimoutputfiles'),
                #TODO: as soon as opts is in settings use line below... and change crab.py
                #"analysisOutputfiles": ", ".join(getOutfiles(self, job, task, flag)),
                "famospath":  self.__formatPath(config.get(CSA, 'famospath')),
                "famosdatapath":  config.get(CSA, 'famosdatapath'),
                # local dbs instance for publication
                "dbsurl":  config.get(CSA, 'dbsurl'),
                # path of all dbsentries
                "dbsfilepath":  self.__formatPath(config.get(CSA, 'dbsfilepath')),
                "storage_element":  config.get(CSA, 'storage_element'),
                "master_list":  [self.__formatPath(i) for i in config.get(CSA, 'master_list').split()],
                "datasets_list":  self.__formatPath(config.get(CSA, 'datasets_list')),
                "jobs_list":  self.__formatPath(config.get(CSA, 'jobs_list')),
                #-- skims
                #"skims": self.__readSkimSections( config )
                #--- private
                "InputTags":{},
                "Analyzers":{},
                "drop":[],
                "keep":[],
                "addKeep": None,
                "selectEvents":"",
                "defaultNumEvents" :-1,
                "additionalProducers":"",
                "makeCountHistos": config.has_option("general" , "makeCountHistos") and config.getboolean("general" , "makeCountHistos")
            }
            if not options == None and "skim" in dir(options) and  options.skim:
                self.getMap()[ "defaultNumEvents" ] = self.getMap()[ "nSkimEvents" ]
            #optimal commands in general section
            for command in ["keep", "drop","selectEvents", "additionalProducers", "addKeep"]:
                if config.has_option("general", command):
                    self.getMap()[ command ] = config.get("general", command)
                    if command in ["keep", "drop", "additionalProducers"]:
                        self.getMap()[ command ] = self.getMap()[ command ].split()
                    if command == "addKeep":
                        for path in  self.getMap()[ command ].split():
                            assert os.path.exists(path), "addKeep file '%s' not found"%os.path.abspath(path)
                            addKeepFile = open(path,"r")
                            for addKeppStatement in addKeepFile.read().splitlines():
                                if addKeppStatement.split()[0] in ["keep","drop"]:
                                    self.getMap()[ addKeppStatement.split()[0] ].append(addKeppStatement.split()[1])

            #optimal commands in CSA section
            for command in ["globalTag","globalTagMc"]:
               if config.has_option(CSA, command):
                   self.getMap()[ command ] = "'%s'"%config.get(CSA, command)                                       
	    print "HIER!", self.master_list	
            for masterListPath in self.master_list:
		    
                if not os.path.exists(masterListPath):
                    raise StandardError, "Could not find master list: '%s'" % self.master_list
            self.getMap()[ "masterConfig" ] = BetterConfigParser()
            self.getMap()[ "masterConfig" ].read(self.master_list)

            if not job == None:
                self.getMap()[ "monteCarloAvailable" ] &= not "Data" in self.getMap()[ "masterConfig"].get(job, 'groups')
			
            if self.getMap()["globalTag"] in ["'auto'"] :
                if self.getMap()[ "monteCarloAvailable" ]:
                    self.getMap()["globalTag"] = "autoCond[ 'mc' ]"
                else:
                    print "WARNING: not sure if 'com10' is right for autoconfigured GlobalTag. look at http://cmssw.cvs.cern.ch/cgi-bin/cmssw.cgi/CMSSW/Configuration/PyReleaseValidation/python/autoCond.py"
                    self.getMap()["globalTag"] = "autoCond[ 'com10' ]"

            if "globalTagMc" in self.getMap():
                if self.getMap()[ "monteCarloAvailable" ]:
                    self.getMap()["globalTag"] = self.getMap()["globalTagMc"]
                    print "using MC global tag '%s'"%self.getMap()["globalTag"]
                    
            for section in config.sections():
                if "InputTags:" in section:
                    collectionName = section.split("InputTags:")[1]
                    self.getMap()["InputTags"][ collectionName ] = {}
                    for option in config.options(section):
                         self.getMap()["InputTags"][ collectionName ][ option ] = config.get(section, option)

            for section in config.sections():
                if section.startswith("Analyzer:"):
                    analyzerName = section.split("Analyzer:")[1]
                    self.getMap()["Analyzers"][ analyzerName ] = {"type":"DiLeptonAnalyzer"}
                    for option in config.options(section):
                         self.getMap()["Analyzers"][ analyzerName ][ option ] = config.get(section, option)

            #read Crab additions blocks (like CMSSW.smothing = something differnt) 
            crabAdditionsBlockNames = ["General", "JobType", "Data", "Site", "User", "Debug"]
            crabAdditionsBlocks = {}
            for blockName in crabAdditionsBlockNames:
                crabAdditionsBlocks["%s-AdditionsBlock" % blockName] = ""
            for option in config.options("crab"):
                if "." in option:
                    sectionName = option.split(".")[0]
                    print option
                    if not "%s-AdditionsBlock" % sectionName in crabAdditionsBlocks:
                       raise StandardError, "could not set crab additions Block for section %s" % sectionName
                    crabAdditionsBlocks["%s-AdditionsBlock" % sectionName] += 'config.%s.%s = "%s"\n' % (sectionName,option.split(".")[1], config.get("crab", option))
            self.getMap()["crabAdditionsBlocks"] = crabAdditionsBlocks

#            for collection in self.getMap()[ "masterConfig" ].options("InputTags:%s" % self.getMap()["InputTagCollection"]):
 #               self.getMap()[ "InputTags" ][ collection ] = config.get("InputTags:%s" % self.InputTagCollection, collection)

            if not options == None:
                #self.getMap()["coreNumber"] = int(options.coreNumber)
                #TODO: it would be nice if values set by hand on command line could be survive the config file default settings...
                #      this can not be done without much effort unless we drop having default values for the optparser :(
                for option, value in options.__dict__.items():
                    self.getMap()[ option ] = value
                    if config.has_option("general", option):
                        self.getMap()[ option ] = config.get("general", option)

    #        if not opts.grid:
    #              self.theMap[ "Submitmode" ] = 'local'
    #        if opts.grid:
    #            if not opts.all:
    #                   self.theMap[ "Submitmode" ] = 'grid'
    #            if opts.all:
    #                   self.theMap[ "Submitmode" ] = 'gridall'
    #            if opts.missing:
    #                   self.theMap[ "Submitmode" ] = 'grfidmissing'

    def tearDown(self):
        del __main__.__dict__[ self.theGlobalName ]

    def getInputTags(self, job):
        result = {}
        for collectionName in self.InputTags:
            #FIXME name of the collection is irrelevant but has to be unique, this bothers ME
            appliesToJob = False
            currentInputTags = {}
            for option in self.InputTags[ collectionName ]:
                optionContent = self.InputTags[ collectionName ][ option ]
                if option.startswith("defaultFor|"):
                    appliesToJob = option.split("defaultFor|")[1] == self.InputTagCollection\
                                    and self.inGroup(optionContent , job)
                else:
                    if option in currentInputTags:
                        raise StandardError, "Overlapping group definition for InputTags! Job '%s' in '%s' and another Collection." % (job, option)
                    currentInputTags[ option ] = optionContent
            if appliesToJob:
                result = currentInputTags
        if result == {}:
            raise StandardError, "No suitable InputTags section found for job: '%s' using InputTagCollection: '%s'" % (job, self.InputTagCollection)

        return result

    def getMap(self):
        '''get whole configuration'''
        if not self.__testSetUp():
            raise StandardError, "MainConfiguration has not been set up!"

        return __main__.__dict__[ self.theGlobalName ]

    def getOutfiles(self, job, tasks=None, flag=None, numbers=None):
        ''' produce list of output files'''
        result = []
        if flag == None: flag = self.flag
        if tasks == None: tasks = self.tasks
        taskName = self.getTaskName(tasks)
        if self.skim:
            rawList = self.skimoutputfiles.replace(",", " ").split()
            if numbers == None:
                result.extend(rawList)
            else:
                for number in numbers:
                    result.extend(["%s_%s" % (file, number) for file in rawList])

        else:
            if numbers == None:
                result.extend(["%s_%s_%s.root" % (flag, taskName, job),
                               "%s_%s_%s.log" % (flag, taskName, job)])
                if not (self.keep == [] and self.drop == []):
                    result.append("%s_%s_%s.EDM.root" % (flag, taskName, job))
            else:
                for number in numbers:
                    result.extend(["%s_%s_%s_%s.root" % (flag, taskName, job, number),
                                   "%s_%s_%s_%s.log" % (flag, taskName, job, number)])
                if not (self.keep == [] and self.drop == []):
                    result.append("%s_%s_%s_%s.EDM.root" % (flag, taskName, job, number))
        return result

    #FIXME: depricated
    #def getCrabDirectory(self, job, task=None, flag=None):
    #    if flag == None: flag = settings.flag
    #    if task == None: task = settings.task
    #    return os.path.join(self.analysispath, "CRABCFG", job, task, flag)

    def getTaskName(self, tasks=None):
        if tasks == None:
            tasks = self.tasks
        result = "".join(tasks)
        if len(result) > 200:
            raise StandardError, "task name gets too long. implent hashing now!"
        return result


    def getCrabDirectory(self, job, tasks=None, flag=None):
        result = None
        if flag == None: flag = self.flag
        if tasks == None: tasks = self.tasks
        if self.skim:
            result = os.path.join(self.skimpath, flag, job)
        else:
            result = os.path.join(self.analysispath, flag, self.getTaskName(tasks), job)
        return result

    def getRawTask(self, name, evalAdditions={}):
        from cmsDummies import InputTag
        settings = MainConfig()
        evalGlobals = {}
        def input(subPath, evalGlobals=evalGlobals): 
            taskPath = None
            for path in self.tasksPath:
                if os.path.exists(os.path.join(path, subPath)):
                    if not taskPath is None:
                        raise StandardError, "Task name '%s' not unique! Found '%s' and '%s"%(subPath, taskPath, os.path.join(path, subPath))
                    taskPath = os.path.join(path, subPath)
    
            if taskPath is None:
                raise StandardError, "could not find task description: %s in %s" % (subPath, self.tasksPath)
            taskFile = open(taskPath, "r")
            result = taskFile.read()
            taskFile.close()
            return eval(result, evalGlobals)

        def condition( cond, resultA, resultB = ""): 
            if cond: return resultA
            else: return resultB

        evalGlobals.update( { "input": input,
                       "condition": condition,
                       "InputTag": InputTag,
                       })
        evalGlobals.update(evalAdditions)
        
        rawTask = input(name, evalGlobals)
        if not "activeFilters" in rawTask:
            raise StandardError, "definition of active filters is missing for task '%s'" % name

        for sequence in rawTask:
            if not len(rawTask[sequence]) > 0 and not sequence == "activeFilters":
                print rawTask[sequence]
                raise StandardError, "malformed cut sequence: %s" % sequence
        return rawTask

    def getAnalyzers(self, type):
        result = {}
        for analyzer in self.getMap()["Analyzers"]:
            if self.getMap()["Analyzers"][analyzer]["type"] == type:
                result.update({analyzer: self.getMap()["Analyzers"][analyzer]})
        return result

    def inGroup(self, groupSelection, jobName):
        '''check if jobName is in groupSelection'''
        rawJobGroups = self.masterConfig.get(jobName, "groups")
        groupMembership = {"All":True}
        for definedGroup in self.groups:
            groupMembership[ definedGroup ] = False

        jobGroups = rawJobGroups.split()
        for jobGroup in jobGroups:
            if not jobGroup in groupMembership:
                raise StandardError, " undefined group %s in job %s" % (jobGroup, jobName)
            groupMembership[ jobGroup ] = True
        return eval(groupSelection, groupMembership)

    def __testSetUp(self):
        '''        test if singleton has been setUp in        '''
        return self.theGlobalName in __main__.__dict__

    def __cleanPaths(self, pathList):
        ''' clean paths of starting spaces'''
        result = []
        for path in pathList:
            while path.startswith(" "):
                path = path[1:]
            result.append(path)
        return result

    def __formatPath(self, path):
        ''' expand variables and make paths absolute '''
        result = os.path.expandvars(path)
        result = os.path.abspath(result)
        return result


#===============================================================================
#                       not in use
#
#    def __readSkimSections(self, config):
#        
#        result = {}
#        for section in config.sections():
#            if section.startswith("skim:"):
#                 result[section.split("skim:")[1]] = {
#                    "cmsswTemplate": config.get(section, "cmsswTemplate"),
#                    "globalDBS": config.get(section, "globalDBS"),
#                    "nEvents": config.get(section, "nEvents")
#                    }
#        print result
#        return result
#===============================================================================

    def __getattr__(self, name):
        '''get single attribute as if it where part of the object'''
        if name in self.__dict__:
            return self.__dict__[ name ]
        else:
            if not "__theMainConfigMap__" in __main__.__dict__:
                raise AttributeError, "tryed to get '%s', but MainConfiguration not set up" % name
            if not name in __main__.__dict__[ "__theMainConfigMap__" ]:
                raise AttributeError, "attribute '%s' not found in configuration" % name
            return __main__.__dict__[ "__theMainConfigMap__" ][ name ]

if __name__ == '__main__':
    os.chdir("..")
    MainConfig(["Input/default.ini"])
    b = MainConfig()
    from pprint import pprint
    pprint(b.getInputTags("SUSY_LM0_Cern"))
    pprint(b.getInputTags("SUSY_LM0_noTrigger"))
    print b.filename
