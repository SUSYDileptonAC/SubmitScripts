# -*- coding: utf-8 -*-
### adapting crab.py to use CRAB3, October 2014 Jan-F. Schulte

import os, subprocess, shutil
#, srmop
import analysis
from mainConfig import MainConfig

def createCRABcfg(Job, Pset, WorkDir, OutputFiles, DBSpath, crabcfg, PublishName=''):
        #TODO get rid of last if statement
        #probably factorize in three sections [CRAB], [CMSSW], [USER]
        settings = MainConfig()
        repMap = {
                "theJob": Job,
                "ParameterSet": Pset,
                "OutputFiles": OutputFiles,
                "datasetpath": DBSpath,
                "workdir": WorkDir,
                "PublishName": PublishName,
                "customDBSBlock": "#no custom DBS",
                "GRID-AdditionsBlock": ""
        }
        
        #put CMSSW.increment_seeds=generator,VtxSmeared for production
        repMap.update(settings.getMap())
        repMap.update(settings.crabAdditionsBlocks)
        repMap["nUnits"] = repMap["units_per_job"]
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
#config.JobType.outputFiles = %(OutputFiles)s
config.JobType.allowUndistributedCMSSW = True
%(JobType-AdditionsBlock)s
config.section_("Data")
config.Data.inputDataset = "%(datasetpath)s"
config.Data.lumiMask = "%(lumi_mask)s"
config.Data.inputDBS = "%(inputDBS)s"
config.Data.splitting = "%(splitting)s"
config.Data.unitsPerJob = %(nUnits)s
config.Data.totalUnits = -1
config.Data.publication = %(publish)s
config.Data.publishDBS = "%(pubDBSURL)s"
config.Data.outputDatasetTag = "%(theJob)s"
config.Data.outLFNDirBase = "%(histogramstoragepath)s"
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
%(additions)s
%(publishBlock)s
"""

        for (job, psetPath) in zip(jobs, psetPaths):
                repMap.update({
                                                "name":job,
                                                "pset":psetPath,
                                                "output_file":", ".join(settings.getOutfiles(job)),
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


