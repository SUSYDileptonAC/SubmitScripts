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
            print configPaths

            config.read(self.__cleanPaths(configPaths))
            CSA = config.get('general', 'CSA')

            __main__.__dict__[ self.theGlobalName ] = {
                #-- general options
                "numCores":6,
                "CSA": CSA,
                "email": os.path.expandvars(config.get("general", 'email')),
                "groups": config.get("general", 'groups').split(),
                
                #-- crab options
                "StageoutSite": config.get("crab", 'StageoutSite'),
                "units_per_job": os.path.expandvars(config.get("crab", 'units_per_job')),            
                "splitting": os.path.expandvars(config.get("crab", 'splitting')),       
                "lumi_mask": os.path.expandvars(config.get("crab", 'lumi_mask')),       
                "additional_input_files": os.path.expandvars(config.get("crab", 'additional_input_files')),     
                "publish": os.path.expandvars(config.get("crab", 'publish')),       
                "pubDBSURL": os.path.expandvars(config.get("crab", 'pubDBSURL')),       
                
                #--CSA specific options
                "monteCarloAvailable": eval(config.get(CSA, 'monteCarloAvailable')), #must be True or False
                "localdatapath":  self.__formatPath(config.get(CSA, 'localdatapath')),
                "analysispath":  self.__formatPath(config.get(CSA, 'analysispath')),
                "localhistopath":  self.__formatPath(config.get(CSA, 'localhistopath')),
                "localjobhistopath":  self.__formatPath(config.get(CSA, 'localjobhistopath')),
                "mergedhistopath": self.__formatPath(config.get(CSA, 'mergedhistopath')),
                "cleaningpath": self.__formatPath(config.get(CSA, 'cleaningpath')),
                "processedpath": self.__formatPath(config.get(CSA, 'processedpath')),
                "treespath": self.__formatPath(config.get(CSA, 'treespath')),
                "tasksPath":  [self.__formatPath(i) for i in config.get(CSA, 'tasksPath').split()],
                "analogpath":  self.__formatPath(config.get(CSA, 'analogpath')),
                "storagepath":  self.__formatPath(config.get(CSA, 'storagepath')),
                "histogramstoragepath":  self.__formatPath(config.get(CSA, 'histogramstoragepath')),
                "histogramoutputpath":  self.__formatPath(config.get(CSA, 'histogramoutputpath')),
                "cmsstoragepath":  config.get(CSA, 'cmsstoragepath'),
                # path of all dbsentries
                "storage_element":  config.get(CSA, 'storage_element'),
                "master_list":  [self.__formatPath(i) for i in config.get(CSA, 'master_list').split()],
                # local dbs instance for publication
                "inputDBS":  config.get(CSA, 'inputDBS'),
                #--- private
                "Analyzers":{},
                "selectEvents":"",
                "defaultNumEvents" :-1,
                "additionalProducers":"",
                "makeCountHistos": config.has_option("general" , "makeCountHistos") and config.getboolean("general" , "makeCountHistos")
            }
            #optimal commands in general section
            for command in ["additionalProducers"]:
                if config.has_option("general", command):
                    self.getMap()[ command ] = config.get("general", command)
                    if command in ["additionalProducers"]:
                        self.getMap()[ command ] = self.getMap()[ command ].split()

            #optional commands in CSA section
            for command in ["globalTag",]:
               if config.has_option(CSA, command):
                   self.getMap()[ command ] = "'%s'"%config.get(CSA, command)                                       
            for masterListPath in self.master_list:
                if not os.path.exists(masterListPath):
                    raise StandardError, "Could not find master list: '%s'" % self.master_list
            self.getMap()[ "masterConfig" ] = BetterConfigParser()
            self.getMap()[ "masterConfig" ].read(self.master_list)

            
            if not job == None:
                self.getMap()[ "monteCarloAvailable" ] &= not "Data" in self.getMap()[ "masterConfig"].get(job, 'groups')
            
            for section in config.sections():
                if section.startswith("Analyzer:"):
                    analyzerName = section.split("Analyzer:")[1]
                    self.getMap()["Analyzers"][ analyzerName ] = {"type":"GenericAnalyzer"}
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

            if not options == None:
                for option, value in options.__dict__.items():
                    self.getMap()[ option ] = value
                    if config.has_option("general", option):
                        self.getMap()[ option ] = config.get("general", option)
                        
        if job is not None:
            # If there is a custom globalTag for a particular data set defined, use it instead of standard GT
            di =  dict(self.getMap()[ "masterConfig" ].items(job))
            if "globalTag" in di:
                self.getMap()["globalTag"] = "'%s'"%(di["globalTag"].strip())
    
    
    

    def tearDown(self):
        del __main__.__dict__[ self.theGlobalName ]

    def getMap(self):
        '''get whole configuration'''
        if not self.__testSetUp():
            raise StandardError, "MainConfiguration has not been set up!"

        return __main__.__dict__[ self.theGlobalName ]

    def getOutfiles(self, job, tasks=None, flag=None):
        ''' produce list of output files'''
        result = []
        if flag == None: flag = self.flag
        if tasks == None: tasks = self.tasks
        taskName = self.getTaskName(tasks)
        result.extend(["%s_%s_%s.root" % (flag, taskName, job),
                       "%s_%s_%s.log" % (flag, taskName, job)])
        return result

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


    def __getattr__(self, name):
        '''get single attribute as if it where part of the object'''
        if name in self.__dict__:
            return self.__dict__[ name ]
        else:
            if not "__theMainConfigMap__" in __main__.__dict__:
                raise AttributeError, "tried to get '%s', but MainConfiguration not set up" % name
            if not name in __main__.__dict__[ "__theMainConfigMap__" ]:
                raise AttributeError, "attribute '%s' not found in configuration" % name
            return __main__.__dict__[ "__theMainConfigMap__" ][ name ]

if __name__ == '__main__':
    pass
