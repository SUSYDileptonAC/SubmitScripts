'''
Created on 26.01.2012

@author: heron
'''

from src.messageLogger import messageLogger as log


class JobDB(object):
    "Factory for jobs, either read from DB or created from root files"

    def __init__(self, config, name):
        from src.helpers import Section
        sectionDefaults = {"name": "JobDBName",
                           "dbPath": "sqlite:jobs.db?timeout=5000",
                           }
        self.section_ = Section(config, name, sectionDefaults)
        self.__connection__ = None
        self.connect()

    def connect(self):
        "connect to db. (at the moment done in __init__)"
        import sqlobject
        from job import SQLJob

        log.logInfo("Setting up DB connection: %s" % self.section_.dbPath)

        self.__connection__ = sqlobject.connectionForURI(self.section_.dbPath)

        #the connection will be closed instead of returning to the pool
        self.__connection__._pool = None
        sqlobject.sqlhub.processConnection = self.__connection__
        #self.__connection__.debug = True

        if not self.__connection__.tableExists("sql_job"):
            SQLJob.createTable(ifNotExists=False)

    def release(self):
        "release lock from db"
        log.logError("releasing the connection is not implemented, yet")
        self.__connected__ = False

    def updateJob(self, job, force=False):
        "write job into db (either create or update)"
        from job import SQLJob, Job
        if self.jobExists(job):
            sqlJobs = SQLJob.selectBy(name=job.name)
            assert sqlJobs.count() < 2, "dublicate name '%s'" % job.name
            sqlJob = sqlJobs.getOne()
            statusHigher = Job.Stati.compare(job.status, sqlJob.status) > 0
            timestampUnaltered = job.timestamp == sqlJob.timestamp if not job.timestamp == None else True

            if (statusHigher and timestampUnaltered) or force:
                sqlJob.update(job)
            elif not statusHigher:
                log.logDebug("skipping '%s' %s <= %s" % (job.name, job.status, sqlJob.status))
            elif not timestampUnaltered:
                log.logError("skipping '%s' %s != %s" % (job.name, job.timestamp, sqlJob.timestamp))
        else:
            sqlJob = SQLJob()
            sqlJob.update(job)

    def deleteJob(self, job):
        "delete Job from db"
        from job import SQLJob
        sqlJobs = SQLJob.selectBy(id=job.id)
        sqlJob = sqlJobs.getOne()
        sqlJob.destroySelf()


    def getJobs(self, **kwargs):
        "get generator for jobs matching the criteria in kwargs (e.g. getJobs(name = 'brot', status = Job.Stati.done)"
        from job import Job, SQLJob
        results = SQLJob.selectBy(**kwargs)
        log.logInfo("Found %i matche(s) for '%s'" % (results.count(), kwargs))
        assert results.count() > 0, "job '%s' not found!" % kwargs
        for sqlJob in results.lazyIter():
            yield Job(sqlJob)

    def countJobs(self, **kwargs):
        "count jobs matchin kwargs"
        from job import SQLJob
        results = SQLJob.selectBy(**kwargs)
        return results.count()

    def getJob(self, name):
        "get Job with name from the db"
        return next(self.getJobs(name=name))

    def claimJob(self, dryRun=False, nJobs=1):
        "claim the next created job. returns Job"
        from job import SQLJob, Job

        lockDirName = None
        if not dryRun:
            lockDirName = SQLJob.lockDB(self.__connection__.filename)
        statusToClaim = Job.Stati.created
        if SQLJob.selectBy(status=Job.Stati.important).count() > 0:
            statusToClaim = Job.Stati.important
            log.logDebug("there are important jobs. Let's claim them!")
        result = []
        unclaimedJobs = SQLJob.selectBy(status=statusToClaim)
        try:
            sqlJobs = []
            #jobsToClaim = unclaimedJobs.count()
            claimedJobs = 0
            for job in unclaimedJobs:
                sqlJobs.append(job)
                claimedJobs += 1
                if claimedJobs >= nJobs:
                    break

            if not dryRun:
                for sqlJob in sqlJobs:
                    sqlJob.status = Job.Stati.claimed
                    sqlJob.sync(ignoreLockDir=lockDirName, unlockDB=(sqlJob == sqlJobs[-1]))
            else:
                log.logDebug("DryRun: not setting jobs to claimed.")

            for sqlJob in sqlJobs:
                result.append(Job(sqlJob))
        except StopIteration:
            log.logWarning("all jobs are done!")
            result = []

        return result

    def jobExists(self, job):
        "test if job of name exists"
        from job import SQLJob
        return SQLJob.selectBy(name=job.name).count() > 0

    #def findJobNames(self, expr): 
    #    "find jobs that match 'expr'"
    #    from match import match
    #    result = []
    #    log.logWarning("JobDB.findJobsNames is depricaed because it is slow :( (called for '%s')"%expr)
    #    
    #    return result

    def getDistinct(self, row, selection={}):
        "get distinct entries in row of selection"
        from sqlobject.sqlbuilder import Select
        from job import SQLJob
        select = Select(getattr(SQLJob.q, row),
                         *[ getattr(SQLJob.q, key) == value for key, value in selection.items()] ,
                         distinct=True)
        sql = self.__connection__.sqlrepr(select)
        return [ i[0] for i in self.__connection__.queryAll(sql)]


    def createJobs(self, scanSection, trees):
        "create jobs from trees in Job.Stati.created status"
        from ROOT import TFile, TH2F
        from itertools import product
        from random import shuffle
        from src.job import Job, SQLJob
        result = []
        histos = self.__get2DHistos__(scanSection, trees)

        statusCounter = 0
        indices = list(product(range(1, scanSection.xBinning[0] + 1),
                                  range(1, scanSection.yBinning[0] + 1)))
        shuffle(indices)

        references = {}
        for formulaName in scanSection.fromReference:
            refPath = getattr(scanSection, "%sReference" % formulaName)
            refFile = TFile.Open(refPath.split(".root/")[0] + ".root")
            references[formulaName] = refFile.Get(refPath.split(".root/")[-1].split("(")[0])
            if "(" in refPath:
                args = list(eval("(" + refPath.split("(")[1]))
                log.logDebug("Drawing reference %s with '%s'" % (formulaName, args))
                tree = references[formulaName]
                targetName = "%sReference" % formulaName
                args[0] += ">> %s" % targetName
                references[formulaName] = TH2F(targetName, targetName, *(scanSection.xBinning + scanSection.yBinning))
                tree.Draw(*args)
                references[formulaName].Draw()

        for binX, binY in indices:
            log.logDebug("adding x = %.2f, y = %.2f" % (binX, binY))
            parameters = {}
            for formulaName, regionChannel in product(histos.keys(), histos[histos.keys()[0]].keys()):
                histo = histos[formulaName][regionChannel]
                if not scanSection.xBinColumn in parameters:
                    if scanSection.xyBinsFromFile:
                        parameters.update({ scanSection.xBinColumn: histo.GetXaxis().GetBinCenter(binX),
                                           scanSection.yBinColumn: histo.GetYaxis().GetBinCenter(binY),
                                           })

                    parameters.update({"status": Job.Stati.created,
                                        "signalRegion": scanSection.signalRegions,
                                       })
                    parameters.update(scanSection.constants)

                if not formulaName in parameters:
                    parameters[formulaName] = {}
                parameters[formulaName][regionChannel] = histo.Integral(binX, binX, binY, binY)

            for formulaName in scanSection.meanForChannels:
                parameters[formulaName] = sum(parameters[formulaName].values()) * 1. / len(parameters[formulaName])

            for formulaName, parameterName in scanSection.fromReference.items():
                if ":" in parameterName:
                    refBinX = references[formulaName].GetXaxis().FindBin(parameters[parameterName.split(":")[1]])
                    refBinY = references[formulaName].GetYaxis().FindBin(parameters[parameterName.split(":")[0]])
                    parameters[formulaName] = references[formulaName].Integral(refBinX, refBinX, refBinY, refBinY)
                    log.logDebug("getting %s form bins '%s': %i" % (formulaName, (refBinX, refBinX, refBinY, refBinY), parameters[formulaName]))
                else:
                    refBinNr = references[formulaName].GetXaxis().FindBin(parameters[parameterName])
                    parameters[formulaName] = references[formulaName].Integral(refBinNr, refBinNr)

            if "jecUp" in parameters and "jecDown" in parameters:
                for key in parameters["jecUp"]:
                    if not "jesUncert" in parameters:
                        parameters["jesUncert"] = {}

                    yields = parameters["yields"][key]
                    jecUp = parameters["jecUp"][key]
                    jecDown = parameters["jecDown"][key]
                    if yields == 0:
                        parameters["jesUncert"][key] = 0
                    else:
                        parameters["jesUncert"][key] = max([abs(1 - i) for i in [jecUp, jecDown]])
                    if not (parameters["jesUncert"][key] <= 1. and parameters["jesUncert"][key] >= 0):
                        log.logDebug("suspicious jesUncert '%s' with jecUp  = '%s', jecDown = '%s' and yields = '%s'" % (parameters["jesUncert"][key], jecUp, jecDown, yields))

            if "ptll" in parameters and "ptllDY" in parameters:
                def llFirst(x, y):
                    if "Tau" in x and not "Tau" in y:
                        return 1
                    if not "Tau" in x and "Tau" in y:
                        return -1
                    else:
                        return 0
                for key in sorted(parameters["ptll"].keys(), cmp=llFirst):
                    if not "signalContamination" in parameters:
                        parameters["signalContamination"] = {}
                    if "Tau" in key:
                        sumTau = sum([parameters["yields"][i] for i in parameters["yields"] if "Tau" in i and " ".join(key.split(" ")[:-1]) in i])
                        if not sumTau > 0: sumTau = 1.
                        sumLLPrediction = sum([parameters["signalContamination"][i] for i in parameters["signalContamination"] if not "Tau" in i and " ".join(key.split(" ")[:-1]) in i])
                        parameters["signalContamination"][key] = scanSection.kTau * sumLLPrediction * parameters["yields"][key] * 1. / sumTau
                    else:
                        parameters["signalContamination"][key] = (parameters["ptll"][key] - parameters["ptllDY"][key])

            if sum(parameters["yields"].values()) == 0:
                log.logDebug("setting job for x = %.2f, y = %.2f to done since there is 0 yield" % (binX, binY))
                parameters["status"] = Job.Stati.ignored
            result.append(Job())
            result[-1].setParameter(parameters)
            statusCounter += 1
            log.statusBar(statusCounter, scanSection.xBinning[0] * scanSection.yBinning[0], message="Jobs created")

        statusCounter = 0
        for newJob in result:
            self.updateJob(newJob)
            statusCounter += 1
            log.statusBar(statusCounter, len(result), message="Jobs saved")



    def __get2DHistos__(self, scanSection, trees):
        "make 2D plots for each of the signal regions, channels and formulas in 'means' option"
        from ROOT import TH2F
        from src.weights import getWeightString as getVertexWeightString
        result = {}
        histoFormulas = {"yields": "1.",
                         "jecUp": "1.",
                         "jecDown": "1.",
                         "ptll":"1.",
                         "ptllDY":"1.",
                         }
        histoFormulas.update(scanSection.means)
        treeCache = {}

        statusCounter = 0
        for formulaName, formula in histoFormulas.items():
            result[formulaName] = {}
            for region in scanSection.signalRegions:
                for channel in scanSection.channels:
                    selection = getattr(scanSection, "cut%s" % region)
                    selection = " %s " % selection
                    selection = "(%s) * (%s) " % (getattr(scanSection, "selection%s" % channel), selection)
                    if formulaName == "jecUp":
                        selection = selection.replace(" ht ", " ( %.4f * ht ) " % (1. + scanSection.jecUncertainty))
                        selection = selection.replace(" met ", " ( %.4f * met ) " % (1. + scanSection.jecUncertainty))

                    if formulaName == "jecDown":
                        selection = selection.replace(" ht ", " ( %.4f * ht ) " % (1. - scanSection.jecUncertainty))
                        selection = selection.replace(" met ", " ( %.4f * met ) " % (1. - scanSection.jecUncertainty))

                    if formulaName in ["ptll", "ptllDY"]:
                        kFactors = eval(getattr(scanSection, "kLL %s" % region))
                        if formulaName == "ptllDY":
                            kFactors *= scanSection.rInOut

                        selection = selection.replace(" met ", " p4.Pt() ")
                        if "EE" in channel or "MuMu" in channel:
                            selection = "(%s) * (met > 75) * %.4f" % (selection, kFactors)
                        else:
                            if formulaName == "ptllDY":
                                kFactors *= -0.5 * (1. / 1.12 + 1.12)
                            selection = "(%s) * (met > 50) * %.4f" % (selection, kFactors)

                    zVeto = scanSection._config.get("cuts", "zVeto")
                    zRegion = scanSection._config.get("cuts", "zRegion")
                    if formulaName == "ptllDY":
                        selection = selection.replace(zVeto, zRegion)
                    elif "EMu" in channel:
                        selection = selection.replace(zVeto, "1")

                    if "Tau" in channel:
                        selection = selection.replace(" ht ", " %s " % scanSection.tauHtBranch)
                        selection = selection.replace(" nJets ", " %s " % scanSection.tauNJetsBranch)
                    else:
                        selection = selection.replace(" ht ", " %s " % scanSection.llHtBranch)
                        selection = selection.replace(" nJets ", " %s " % scanSection.llNJetsBranch)

                    tree = trees[channel]
                    if formulaName not in ["jecUp", "jecDown", "ptll", "ptllDY"]:
                        if not (channel, selection) in treeCache:
                            treeCache[(channel, selection)] = trees[channel].CopyTree(selection)
                        tree = treeCache[(channel, selection)]

                    vertexWeight = scanSection.vertexWeight
                    if vertexWeight == "fromPickel":
                        vertexWeight = getVertexWeightString()

                    #selection = "(%s) * weight * (%s)" % (selection, formula) 
                    selection = "( %s ) * (%s) * (%s)" % (selection, vertexWeight, formula)
                    #selection = "(%s) * weight" % selection# * (%s)" % (selection, formula)

                    targetName = "%s %s %s %s histo" % (scanSection.name, region, channel, formulaName)
                    result[formulaName]["%s %s" % (region, channel)] = TH2F(targetName, targetName,
                                                                            *(scanSection.xBinning + scanSection.yBinning))
                    targetHisto = result[formulaName]["%s %s" % (region, channel)]
                    log.logDebug("For %s %s %s use cut: '%s'" % (formulaName, region, channel, selection))
                    if formulaName in ["ptll", "ptllDY"] and "Tau" in channel:
                        log.logDebug("skipping ptll histos for taus. this is taken from light leptons!")
                    else:
                        tree.Draw("%s:%s>>%s" % (scanSection.yBinName, scanSection.xBinName, targetName), selection)
                    log.logDebug("got %i events!" % (result[formulaName]["%s %s" % (region, channel)].GetEntries()))
                    statusCounter += 1
                    log.statusBar(statusCounter, len(scanSection.channels) * len(scanSection.signalRegions) * len(histoFormulas.items()), message="2D Histos")
                    #result[formulaName]["%s %s" % (region, channel)] = targetHisto
        #print result["xSection"]["SR1 EE"].GetBinContent(1, 1)
        for formulaName in result:
            for regionChannel in result[formulaName]:
                if not formulaName in ["yields", "ptll", "ptllDY"]:
                    result[formulaName][regionChannel].Divide(result["yields"][regionChannel])

        return result






