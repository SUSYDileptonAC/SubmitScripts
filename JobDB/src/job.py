'''
Created on 20.01.2012

@author: epsilon
'''

from messageLogger import messageLogger as log
import os
import sqlobject
from datacard import DataCard
import tempfile
import shutil


class Job(object):
    '''
    classdocs
    '''
    class Stati:
        created = "created"
        important = "important"
        claimed = "claimed"
        done = "done"
        ignored = "ignored"

        @classmethod
        def toColor(cls, status):
            colors = {
                      cls.ignored:1,
                      cls.created: 2,
                      cls.important: 3,
                      cls.claimed: 4,
                      cls.done: 5,
                      }
            for name in dir(cls):
                if not name.startswith("_") and not name in colors:
                    colors[name] = len(colors)
            return colors[status]

        @classmethod
        def compare(cls, a, b):
            order = [cls.ignored, cls.created, cls.important,
                     cls.claimed, cls.done]
            return order.index(a) - order.index(b)

    def __init__(self, sqlJob=None):
        '''
        Constructor
        '''
        from copy import deepcopy
        #cls.status = None
        self.__nameTemplate__ = "%(scanName)s_%(m0).1f_%(m12).1f_%(tanBeta).1f_%(mGluino).1f_%(mSquark).1f"
        self.__rates__ = {}
        self.__signalContaminationRates__ = {}
        self.__channels__ = ["EE", "EMu", "MuMu", "ETau", "MuTau", "TauTau"]
        self.__tempDir__ = None
        self.__refinedJesUncert__ = {}
        self.__refinedPdfUncert__ = {}
        self.__sfFraction__ = None
        self.parameters = {
                           #internal db id (needed in case of dublication or database erros)
                           'id':-1,
                           # point parameters
                           'm0': None,
                           'm12': None,
                           'A0': None,
                           'tanBeta': None,
                           'signMu': None,
                           'mGluino': None,
                           'mSquark': None,
                           # point-related parameters
                           'xSection': None,
                           'xSectionNLO': {},
                           'xSectionNLOUncert': {},
                           'kFactor': {},
                           'genEfficiency': {},
                           # event yields
                           'nEvents': None,
                           'yields': {},
                           #errors
                           'jesUncert':{},
                           'pdfUncert': {},
                           'signalContamination': {},
                           # job 
                           'name': None,
                           'status': None,
                           'version': None,
                           'configTag': None,
                           'scanName': None,
                           'signalRegion': [],
                           'timestamp': None,
                           # limits
                           'limitExpected':-1.0,
                           'limitExpected1SigmaUp':-1.0,
                           'limitExpected1SigmaDown':-1.0,
                           'limitExpected2SigmaUp':-1.0,
                           'limitExpected2SigmaDown':-1.0,
                           'limitExpectedStatUncert':-1.0,
                           'limitObserved':-1.0,
                           'limitObservedStatUncert':-1.0,
                           }

        if (sqlJob != None):
            log.logDebug("Creating Job from SQLJob")
            for name in self.parameters:
                parameter = deepcopy(getattr(sqlJob, name))
                if type(self.parameters[name]) in [dict, list]:
                    log.logDebug("init %s: %s" % (name, parameter))
                    parameter = eval(parameter)
                self.parameters[name] = parameter
            if "yields" in self.parameters:
                self.__channels__ = list(set([i.split()[-1] for i in self.yields.keys()]))

    @property
    def refinedJesUncert(self):
        if (self.__refinedJesUncert__ == {}):
            channelCluster = {
                          'LLSF': ["EE", "MuMu"],
                          'LLOF': ["EMu"],
                          'Taus': ["ETau", "MuTau", "TauTau"],
                          }

            for signalRegion in self.signalRegion:
                for cluster in channelCluster.keys():
                    jesUncert = 0.0
                    totalYield = 0.0
                    for channel in channelCluster[cluster]:
                        key = "%s %s" % (signalRegion, channel)
                        jesUncert += self.jesUncert[key] * self.yields[key]
                        totalYield += self.yields[key]
                        #log.logDebug("JES: %s (%f)" % (self.jesUncert[key], self.yields[key]))

                    if (totalYield > 0.0):
                        jesUncert = 1.0 * jesUncert / totalYield + 1.0
                    else:
                        jesUncert = 1.0

                    clusterKey = "%s %s" % (signalRegion, cluster)
                    #log.logDebug("FinalJES: %f" % (jesUncert))
                    self.__refinedJesUncert__.update({clusterKey: jesUncert})

        return self.__refinedJesUncert__

    @property
    def refinedPdfUncert(self):
        if (self.__refinedPdfUncert__ == {}):
            channelCluster = {
                          'LLSF': ["EE", "MuMu"],
                          'LLOF': ["EMu"],
                          'Taus': ["ETau", "MuTau", "TauTau"],
                          }

            for signalRegion in self.signalRegion:
                for cluster in channelCluster.keys():
                    pdfUncert = 0.0
                    totalYield = 0.0
                    for channel in channelCluster[cluster]:
                        key = "%s %s" % (signalRegion, channel)
                        pdfUncert += self.pdfUncert[key] * self.yields[key]
                        totalYield += self.yields[key]
                        #log.logDebug("PDF: %s (%f)" % (self.pdfUncert[key], self.yields[key]))

                    if (totalYield > 0.0):
                        pdfUncert = 1.0 * pdfUncert / totalYield + 1.0
                    else:
                        pdfUncert = 1.0

                    clusterKey = "%s %s" % (signalRegion, cluster)
                    #log.logDebug("FinalPDF: %f" % (pdfUncert))
                    self.__refinedPdfUncert__.update({clusterKey: pdfUncert})

        return self.__refinedPdfUncert__

    @property
    def rates(self):
        if self.__rates__ == {}:
            self.__rates__ = self.__calcRate__(self.yields)
        return self.__rates__

    @property
    def effTimesAcc(self):
        return self.__calcEffTimesAcc__(self.yields)

    @property
    def observedXSecLimit(self):
        result = .0
        if self.limitObserved > 0:
            result = self.xSection * self.limitObserved
        return result

    @property
    def jesUncertainty(self):
        return self.__weighForSums__(self.jesUncert)

    @property
    def pdfUncertainty(self):
        return self.__weighForSums__(self.pdfUncert)

    @property
    def signalContaminationRates(self):
        if self.__signalContaminationRates__ == {}:
            self.__signalContaminationRates__ = self.__calcRate__(self.signalContamination)
        return self.__signalContaminationRates__


    @property
    def sfFraction(self):
        if (self.__sfFraction__ == None):
            sfRate = 0.0
            totalRate = 0.0
            for signalRegion in self.signalRegion:
                #if (signalRegion == "SR2"):
                    totalRate += self.rates["%s %s" % (signalRegion, 'EE')]
                    totalRate += self.rates["%s %s" % (signalRegion, 'EMu')]
                    totalRate += self.rates["%s %s" % (signalRegion, 'MuMu')]
                    sfRate += self.rates["%s %s" % (signalRegion, 'EE')]
                    sfRate += self.rates["%s %s" % (signalRegion, 'MuMu')]
            if (totalRate != 0.0):
                self.__sfFraction__ = 1.0 * sfRate / totalRate
            else:
                self.__sfFraction__ = 0.0

        return self.__sfFraction__

    @property
    def tauFraction(self):
        numerator = sum([self.rates[i] for i in self.rates if "Tau" in i])
        denominator = sum([self.rates[i] for i in self.rates])
        denominator = denominator if denominator != 0 else -1.
        return numerator * 1. / denominator

    @property
    def signalContaminationFractions(self):
        result = {}
        for key in self.signalContaminationRates:
            result[key] = self.signalContaminationRates[key] * 1. / self.rates[key] if self.rates[key] > 0 else 0.
        return self.__weighForSums__(result)

    @property
    def statusColor(self):
        return self.Stati.toColor(self.status)

    @property
    def exclusionObserved(self):
        result = 0.

        if self.limitObserved >= 0 and self.limitObserved < 1.:
            result = 1.
        elif self.limitObserved >= 1.:
            result = -1
        else:
            result = 0.
        return result

    @property
    def tempDir(self):
        if (self.__tempDir__ == None):
            self.__tempDir__ = tempfile.mkdtemp(dir="/tmp")
            log.logInfo("TempDir: %s" % self.__tempDir__)

        return self.__tempDir__


    def run(self, dryRun=False, keepTemp=False):
        log.logHighlighted("Running job")
        configTag = self.getParameter("configTag")
        dataCards = []
        baseName = "%s_Hybrid" % (configTag)

        # temp dir
        oldDir = os.getcwd()
        log.logDebug("Old dir: %s" % oldDir)
        os.chdir(self.tempDir)

        for signalRegion in self.getParameter('signalRegion'):
            dcName = "%s_%s_datacard.txt" % (configTag, signalRegion)
            log.logInfo("Including DataCard: %s" % dcName)
            dataCards.append(dcName)

        #command = "lands.exe -M Hybrid"
        landsPath = "/net/scratch_cms1b1/cms/user/susyCommon/LandS/test"
        #landsPath = "/Volumes/Data/SUSY/LandS/test"
        logfile = "%s_lands.log" % (configTag)
        hintMethod = "Bayesian"
        command = "%s/lands.exe -M Hybrid --freq --ExpectationHints %s --scanRs 1 --freq --nToysForCLsb 3000 --nToysForCLb 1500 --seed 1234 --doExpectation 1 -t 1000 -n %s -d" % (landsPath, hintMethod, baseName)
        for dataCard in dataCards:
            command = "%s %s" % (command, dataCard)
        command = "%s | tee %s" % (command, logfile)

        fitMacroPath = "%s/fitRvsCLs.C+" % landsPath
        tempFile = "%s.tmp" % (baseName)
        # write root command file
        command2 = """echo -e 'run("%s_m2lnQ.root","plot") \n .q \n' |tee %s""" % (baseName, tempFile)
        # execute root fit macro
        command3 = "root -b -l -C %s < %s |tee -a %s" % (fitMacroPath, tempFile, logfile)


        log.logInfo("Executing: %s" % command)
        if (not dryRun):
            os.system(command)
            log.logInfo("Executing: %s" % command2)
            os.system(command2)
            log.logInfo("Executing: %s" % command3)
            os.system(command3)
            limits = self._parseLandSResult(logfile)

            #exp1SigmaUpError = self._parseNumber(limits['exp1SigmaUpError'])
            #exp1SigmaDownError = self._parseNumber(limits['exp1SigmaDownError'])
            #exp2SigmaUpError = self._parseNumber(limits['exp2SigmaUpError'])
            #exp2SigmaDownError = self._parseNumber(limits['exp2SigmaDownError'])

            dict = {
                    'limitObserved': self._parseNumber(limits['obsValue']),
                    'limitObservedStatUncert': self._parseNumber(limits['obsError']),
                    'limitExpected': self._parseNumber(limits['expValue']),
                    'limitExpectedStatUncert': self._parseNumber(limits['expError']),
                    'limitExpected1SigmaUp': self._parseNumber(limits['exp1SigmaUpValue']),
                    'limitExpected1SigmaDown': self._parseNumber(limits['exp1SigmaDownValue']),
                    'limitExpected2SigmaUp': self._parseNumber(limits['exp2SigmaUpValue']),
                    'limitExpected2SigmaDown': self._parseNumber(limits['exp2SigmaDownValue']),
                    }

            log.logHighlighted("obs = %f" % dict['limitObserved'])
            log.logHighlighted("obsStatError = %f" % dict['limitObservedStatUncert'])
            log.logHighlighted("exp = %f" % dict['limitExpected'])
            log.logHighlighted("expStatError = %f" % dict['limitExpectedStatUncert'])
            log.logHighlighted("exp1SigmaUp = %f" % dict['limitExpected1SigmaUp'])
            log.logHighlighted("exp1SigmaDown = %f" % dict['limitExpected1SigmaDown'])
            log.logHighlighted("exp2SigmaUp = %f" % dict['limitExpected2SigmaUp'])
            log.logHighlighted("exp2SigmaDown = %f" % dict['limitExpected2SigmaDown'])

            log.logInfo("Updating job parameters")
            self.setParameter(dict)
        else:
            log.logInfo("DryRun -- not running.")
            log.logInfo("Not executing: %s" % command2)
            log.logInfo("Not executing: %s" % command3)

        log.logInfo("Done.")

        os.chdir(oldDir)
        if (not keepTemp):
            log.logDebug("Removing %s" % self.tempDir)
            shutil.rmtree(self.tempDir)
            self.__tempDir__ = None
        else:
            log.logDebug("Not removing %s" % self.tempDir)

        return


    def _parseNumber(self, number):
        value = None
        if (number == "nan"):
            value = -2.0
        else:
            value = float(number)
        return value

    def getParameter(self, name=None):
        value = None
        if (name == None):
            value = self.parameters
        else:
            value = self.parameters[name]

        return value


    def setParameter(self, dct):
        self.parameters.update(dct)
        self.parameters["name"] = self.__nameTemplate__ % self.parameters


    def makeDataCard(self):
        log.logInfo("Making DataCard")

        configTag = self.getParameter("configTag")
        configFile = "datacard_%s.ini" % (configTag)
        version = self.getParameter("version")

        if (configTag == None):
            log.logError("Cannot make DataCard: configTag is not set.")
            return

        if (version == None):
            log.logError("Cannot make DataCard: version is not set.")
            return

        from src.helpers import BetterConfigParser
        configParser = BetterConfigParser()
        configParser.read(configFile)

        log.logDebug("configTag: %s, version: %s" % (configTag, version))

        for signalRegion in self.getParameter('signalRegion'):
            for channel in self.__channels__:
                key = "%s %s" % (signalRegion, channel)

                # make yields available in ini file
                sectionName = "DB_Rates:%s" % channel
                if (not configParser.has_section(sectionName)):
                    configParser.add_section(sectionName)

                rate = self.rates[key]
                configParser.set(sectionName, signalRegion, rate)

                # make signal contamination available in ini file
                sectionName = "DB_SignalContRates:%s" % channel
                if (not configParser.has_section(sectionName)):
                    configParser.add_section(sectionName)

                rate = self.signalContaminationRates[key]
                configParser.set(sectionName, signalRegion, rate)

            # make JES uncertainties available in ini file
            sectionName = "DB_JES:LLSF"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedJesUncert["%s LLSF" % signalRegion])

            sectionName = "DB_JES:LLOF"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedJesUncert["%s LLOF" % signalRegion])

            sectionName = "DB_JES:Taus"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedJesUncert["%s Taus" % signalRegion])

            # make PDF uncertainties available in ini file
            sectionName = "DB_PDF:LLSF"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedPdfUncert["%s LLSF" % signalRegion])

            sectionName = "DB_PDF:LLOF"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedPdfUncert["%s LLOF" % signalRegion])

            sectionName = "DB_PDF:Taus"
            if (not configParser.has_section(sectionName)):
                configParser.add_section(sectionName)
            configParser.set(sectionName, signalRegion, self.refinedPdfUncert["%s Taus" % signalRegion])


        # temp dir
        oldDir = os.getcwd()
        os.chdir(self.tempDir)

        # loop signal regions and make DataCards
        for signalRegion in self.getParameter('signalRegion'):
            log.logHighlighted("Preparing DataCard for region: %s" % signalRegion)
            dcName = "%s_%s" % (configTag, signalRegion)

            pointSectionName = "DB_Point"
            if (not configParser.has_section(pointSectionName)):
                configParser.add_section(pointSectionName)
            configParser.set(pointSectionName, "signalRegion", signalRegion)

            DataCard.makeDataCard(configParser, name=dcName)

        os.chdir(oldDir)
        return


    def _parseLandSResult(self, logfile):
        log.logInfo("Parsing LandS result")

        logFile = open(logfile, "r")
        rawInput = logFile.read()
        logFile.close()

        floatExpr = "([-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?|nan)"
        floatError = "(?P<%%sValue>%s)\+\/\-(?P<%%sError>%s)" % (floatExpr, floatExpr)
        parselines = [#"Observed data limit: (?P<obsValue>[0-9]*\.[0-9]*) \+\/\- (?P<obsError>[0-9]*\.[0-9]*)",
                     #"expected median limit: (?P<expValue>[0-9]*\.[0-9]*) \+\/\- (?P<expError>[0-9]*\.[0-9]*)"
                     #"EXPECTED LIMIT BANDS from\(obs, -2s,-1s,median,1s,2s\) mass= -1: (?P<obsValue>[0-9]*\.[0-9]*|0)\+\/\-(?P<obsError>[0-9]*\.[0-9]*|nan|0), ([0-9]*\.[0-9]*|0)\+\/\-([0-9]*\.[0-9]*|nan|0), (?P<exp1SigmaDown>[0-9]*\.[0-9]*|0)\+\/\-(?P<exp1SigmaDownError>[0-9]*\.[0-9]*|nan|0), (?P<expValue>[0-9]*\.[0-9]*|0)\+\/\-(?P<expError>[0-9]*\.[0-9]*|nan|0), (?P<exp1SigmaUp>[0-9]*\.[0-9]*|0)\+\/\-(?P<exp1SigmaUpError>[0-9]*\.[0-9]*|nan|0), ([0-9]*\.[0-9]*|0)\+\/\-([0-9]*\.[0-9]|nan|0)*"
                     "EXPECTED LIMIT BANDS from\(obs, -2s,-1s,median,1s,2s\) mass= -1: %s, %s, %s, %s, %s, %s" % (floatError % ("obs", "obs"),
                                                                                                                  floatError % ("exp2SigmaDown", "exp2SigmaDown"),
                                                                                                                  floatError % ("exp1SigmaDown", "exp1SigmaDown"),
                                                                                                                  floatError % ("exp", "exp"),
                                                                                                                  floatError % ("exp1SigmaUp", "exp1SigmaUp"),
                                                                                                                  floatError % ("exp2SigmaUp", "exp2SigmaUp")
                                                                                                                  )
                     ]
        limits = {}
        from re import match
        for line in rawInput.splitlines():
            for parseline in parselines:
                matchResult = match(parseline, line)
                if matchResult != None:
                    limits.update(matchResult.groupdict())

        log.logInfo("Result: %s" % limits)
        return limits

    def __weighForSums__(self, target):
        result = {}
        for key in target:
            regionName = " ".join(key.split(" ")[:-1])
            denom = sum([self.yields[i] for i in target if ("Tau" in i) == ("Tau" in key) and regionName in i])
            result[key] = target[key] * (self.yields[key] * 1. / denom) if denom > 0 else 0.
        return result

    def __calcEffTimesAcc__(self, numEvents):
        from itertools import product
        result = {}
        nTotal = self.nEvents
        genEfficiency = self.genEfficiency
        for signalRegion, channel in product(self.signalRegion, self.__channels__):
            key = "%s %s" % (signalRegion, channel)
            log.logDebug("Key: %s" % key)
            log.logDebug("yield: %.3f, genEfficiency: %.3f, nTotal: %.3f" % (numEvents[key], genEfficiency[key], nTotal))
            result[key] = numEvents[key] * genEfficiency[key] * 1. / nTotal if nTotal > 0 else 0.
        return result

    def __calcRate__(self, numEvents):
        from itertools import product
        result = {}
        # insert DB info
        xSection = self.xSection
        kFactor = self.kFactor
        luminosity = 4980.

        effTimesAcc = self.__calcEffTimesAcc__(numEvents)

        for signalRegion, channel in product(self.signalRegion, self.__channels__):
            key = "%s %s" % (signalRegion, channel)

            rate = effTimesAcc[key] * xSection * luminosity
            log.logDebug("Key: %s" % key)
            log.logDebug("yield: %.3f, eff x acc: %.3f, xSection: %.3f, lumi: %.3f" % (numEvents[key], effTimesAcc[key] , xSection, luminosity))
            if (kFactor != None and kFactor.has_key(key)):
                log.logDebug("Using kFactor: %f" % kFactor[key])
                rate *= kFactor[key]
            result[key] = rate
        return result


    def __str__(self):
        return "Job(%s)" % self.parameters

    def __getattr__(self, name):
        result = None
        if name in self.__dict__:
            result = self.__dict__[name]
        elif name in self.parameters:
            result = self.getParameter(name)
        return result


class SQLJob(sqlobject.SQLObject):
    '''
    classdocs
    '''
    class sqlmeta:
        lazyUpdate = True

    # point parameters
    m0 = sqlobject.FloatCol(default=None)
    m12 = sqlobject.FloatCol(default=None)
    A0 = sqlobject.FloatCol(default=None)
    tanBeta = sqlobject.FloatCol(default=None)
    signMu = sqlobject.FloatCol(default=None)
    mGluino = sqlobject.FloatCol(default=None)
    mSquark = sqlobject.FloatCol(default=None)
    # point-related parameters
    xSection = sqlobject.FloatCol(default=None)
    xSectionNLO = sqlobject.StringCol(default="{}")
    xSectionNLOUncert = sqlobject.StringCol(default="{}")
    kFactor = sqlobject.StringCol(default="{}")
    genEfficiency = sqlobject.StringCol(default="{}")
    # event yields
    nEvents = sqlobject.IntCol(default=None)
    yields = sqlobject.StringCol(default="{}")
    #errors
    signalContamination = sqlobject.StringCol(default="{}")
    pdfUncert = sqlobject.StringCol(default="{}")
    jesUncert = sqlobject.StringCol(default="{}")
    # job
    name = sqlobject.StringCol(default=None)
    status = sqlobject.StringCol(default=None)
    version = sqlobject.StringCol(default=None)
    configTag = sqlobject.StringCol(default=None)
    scanName = sqlobject.StringCol(default=None)
    signalRegion = sqlobject.StringCol(default=None)
    timestamp = sqlobject.StringCol(default=None)
    # limits
    limitExpected = sqlobject.FloatCol(default= -1.0)
    limitExpected1SigmaUp = sqlobject.FloatCol(default= -1.0)
    limitExpected1SigmaDown = sqlobject.FloatCol(default= -1.0)
    limitExpected2SigmaUp = sqlobject.FloatCol(default= -1.0)
    limitExpected2SigmaDown = sqlobject.FloatCol(default= -1.0)
    limitExpectedStatUncert = sqlobject.FloatCol(default= -1.0)
    limitObserved = sqlobject.FloatCol(default= -1.0)
    limitObservedStatUncert = sqlobject.FloatCol(default= -1.0)


    def __init__(self, **kwargs):
        '''
        Constructor
        '''

        if len(kwargs) == 0:
            log.logDebug("Creating new empty SQLJob")
            dct = {
                           # point parameters
                           'm0': None,
                           'm12': None,
                           'A0': None,
                           'tanBeta': None,
                           'signMu': None,
                           'mGluino': None,
                           'mSquark': None,
                           # point-related parameters
                           'xSection': None,
                           'xSectionNLO': None,
                           'xSectionNLOUncert': None,
                           'kFactor': None,
                           'genEfficiency': None,
                           # event yields
                           'nEvents': None,
                           'yields': None,
                           #erros
                           'signalContramination': None,
                           'pdfUncert': None,
                           'jesUncert': None,
                           # job 
                           'name': None,
                           'status': None,
                           'version': None,
                           'configTag': None,
                           'scanName': None,
                           'signalRegion': None,
                           'timestamp': None,
                           # limits
                           'limitExpected':-1.0,
                           'limitExpected1SigmaUp':-1.0,
                           'limitExpected1SigmaDown':-1.0,
                           'limitExpected2SigmaUp':-1.0,
                           'limitExpected2SigmaDown':-1.0,
                           'limitExpectedStatUncert':-1.0,
                           'limitObserved':-1.0,
                           'limitObservedStatUncert':-1.0,
                           }
        sqlobject.SQLObject.__init__(self, **kwargs)

        #log.logDebug("Creating new SQLJob")
        #for parameter in dct.keys():
            #log.logDebug("parameter: %s" % parameter)
        #    setattr(self, parameter, dct[parameter])
        return

    def update(self, job):
        for key, option in job.parameters.items():
            if type(option) in [dict, list]:
                option = repr(option)
            if not key == "id":
                setattr(self, key, option)
        self.sync()

    @classmethod
    def lockDB(cls, dbPath):
        from time import sleep
        from os import mkdir
        sleepTime = 4.5
        lockDirName = "%s.lock" % (dbPath)
        locked = False
        while not locked:
            try:
                mkdir(lockDirName)
                locked = True
            except OSError:
                locked = False
                log.logInfo("waiting for lock on '%s'" % (dbPath))
                sleep(sleepTime)

        return lockDirName



    def sync(self, ignoreLockDir=None, unlockDB=True):
        from os import rmdir
        from time import ctime

        lockDirName = ignoreLockDir
        if ignoreLockDir == None:
            lockDirName = SQLJob.lockDB(self._connection.filename)

        self.timestamp = "%s" % ctime()
        log.logDebug("starting to sync: %s" % ctime())
        result = sqlobject.SQLObject.sync(self)
        log.logDebug("finished to syncing: %s" % ctime())

        if (unlockDB):
            rmdir(lockDirName)
            log.logDebug("release '%s'" % self._connection.filename)
        return result


