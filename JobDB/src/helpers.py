'''
Created on 18.08.2009

@author: heron
'''
#-------------  need to put this in its own package some time
import ConfigParser
import re
class BetterConfigParser(ConfigParser.ConfigParser):
    def __init__(self, defaults=None):#in python 2.6, dict_type=dict):
        self.__runtimeRepMap = {}
        self._activeSection = None
        self._cache = {}
        ConfigParser.ConfigParser.__init__(self, defaults)#, dict_type)            

    def get(self, section, option, raw=True, default=None, sectionwideReplace=True):
        result = None
        if (section, option) in self._cache:
            result = self._cache[(section, option, self._activeSection)]
        else:
            matchedName = None
            for name, item in self.items(section, raw=raw):
                #print name, option, re.match(name+"$", option)
                if re.match(name + "$", option) != None:
                    assert matchedName == None, "option '%s' matches '%s' and '%s'" % (option, matchedName, name)
                    matchedName = name
                    result = item
            if matchedName == None:
                if not default is None:
                    result = default
                if self.has_option(section, "default"):
                    result = self.get(section, "default", raw=raw)
            if sectionwideReplace and "splitlines" in dir(result):
                result = "\n".join([self.__replaceSectionwideTemplates(l) for l in result.splitlines()])
                result = result.replace("\<", "<")
            #not sure if I have created achicken egg problem here
            for entry in self.__runtimeRepMap:
                if "replace" in dir(result):
                    result = result.replace(".oO[%s]Oo." % entry, self.__runtimeRepMap[entry])
                if "__setitem__" in dir(result):
                    for i in range(len(result)):
                        if "replace" in dir(result[i]):
                            result[i] = result[i].replace(".oO[%s]Oo." % entry, self.__runtimeRepMap[entry])
            self._cache[(section, option, self._activeSection)] = result
        return result

    #def set(self, section, option, value):
    #    self._cache[(section,option)] = value
    #    return ConfigParser.ConfigParser.get(self, section, option, value)


# need to look this syntax up once I am back online...
#    def items(self, **opts):
#        opts["raw"] = True
#        return ConfigParser.ConfigParser.itmes(self, **opts)

    def optionxform(self, optionstr):
        '''enable case sensitive options in .ini files'''
        return optionstr

    def write(self, fileObject):
        for section in self.sections():
            for option in self.options(section):
                self.set(section, option, self.get(section, option, raw=True, sectionwideReplace=False))
        ConfigParser.ConfigParser.write(self, fileObject)

    def addRuntimeReplacement(self, entry, replacement):
        if entry in self.__runtimeRepMap:
            raise StandardError, "'%s' is already in the runtime replacements. You are not allowed to modify!" % entry
        self.__runtimeRepMap[entry] = replacement

    def __replaceSectionwideTemplates(self, data):
        '''replace <section|option> with get(section,option) recursivly'''
        data = str(data)
        result = data
        findExpression = re.compile("((.*)\<(?<!\\\<)([^\>\(\)]*)\|([^\>]*)\>(.*))*")

        groups = findExpression.search(data).groups()
        sectionName = groups[2]
        if not self._activeSection == None and sectionName == "activeSection":
            sectionName = self._activeSection
        if not self.has_section(sectionName) and not sectionName == None:
            assert (not self._activeSection == None) or (not sectionName == "activeSection"), "trying to access undifined active section: '%s'" % data
            #print "WARNING: skipping '%s' in '%s' because section could not be found"%(sectionName, data)
        if not groups == (None, None, None, None, None) and self.has_section(sectionName): # expression not matched
            result = self.__replaceSectionwideTemplates(groups[1])
            matchedName = None
            for name, item in self.items(sectionName, raw=True):
                if not "$" in name: name += "$"
                if re.match(name, groups[3]) != None:
                    if item == "passedString": result = "%s%s" % (result, self.__replaceSectionwideTemplates(groups[3]))
                    else: result = "%s%s" % (result, self.__replaceSectionwideTemplates(item))
                    if not matchedName == None and len(name) > len(matchedName):
                        print "WARNING: ambiguous matching: '<%s|%s>' did not only match '%s' but also '%s'" % (sectionName, groups[3], name, matchedName)
                        machtedName = name
                    else:
                        assert matchedName == None, " '<%s|%s>' did not only match '%s' but also '%s'" % (sectionName, groups[3], name, matchedName)
                        matchedName = name

            if matchedName == None:
                if self.has_option(sectionName, "default"):
                    if self.get(sectionName, "default") == "passedString":
                        result = "%s%s" % (result, self.__replaceSectionwideTemplates(groups[3]))
                    else:
                        result = "%s%s" % (result, self.__replaceSectionwideTemplates(self.get(sectionName, "default")))
                elif self.has_option(sectionName, "defaultSections"):
                    defaultSections = self.get(sectionName, "defaultSections").split()
                    defaultResult = None
                    for defaultSection in defaultSections:
                        if not self.get("default:%s" % defaultSection, groups[3]) == None:
                            defaultResult = self.get("default:%s" % defaultSection, groups[3])
                    assert defaultResult != None, "could not find default for '%s' in '%s' or any defaultSection in '%s'" % (groups[3], sectionName, defaultSections)
                    result = "%s%s" % (result, defaultResult)
                else:
                    #rethrow exception for the poor
                    assert self.has_option(sectionName, groups[3]), "could not find '%s' in section '%s' needed in '%s' (activeSection is '%s')" % (groups[3], sectionName, data, self._activeSection)
                    result = "%s%s" % (result, self.get(sectionName, groups[3]))
            result = "%s%s" % (result, self.__replaceSectionwideTemplates(groups[4]))
        if not findExpression.match(result).groups() == (None, None, None, None, None):
            if not sectionName == None and not self.has_option(sectionName, groups[3]):
                result = "<%s|%s>" % (sectionName, groups[3])
            else:
                result = self.__replaceSectionwideTemplates(result)
        assert not result == None, "something went wrong converting '%s'" % data
        return result

    def setActiveSection(self, name=None):
        from copy import deepcopy
        before = deepcopy(self._activeSection)
        self._activeSection = name
        return before

class Section:
    def __init__(self, config, name, defaults={}):
        self._config = config
        self._name = name
        self._defaults = {"defaultSections":[]}
        self.setDefaults(defaults)
        self.evalGlobals = {}

    def setDefaults(self, defaults):
        for name, newValue in defaults.iteritems():
                #print self._defaults[name], newValue
            if name in self._defaults:
                self._defaults[name] = self.__convert(newValue, self._defaults[name])
            else:
                self._defaults[name] = newValue

    def __str__(self):
        result = "Section: '%s'\n" % self._name
        for i in self._config.options(self._name):
            result += "%s = %s\n" % (i, getattr(self, i))
        for defaultSection in self.defaultSections:
            result += "From Default '%s'\n" % defaultSection
            for i in self._config.options("default:%s" % defaultSection):
                result += "%s = %s\n" % (i, getattr(self, i))
        return result

    def __convert(self, read, default):
        result = None
        if type(default) in [float, int, bool]:
            result = eval(read, self.evalGlobals)
        elif type(default) in [list, bool]:
            try:
                result = eval(read, self.evalGlobals)
            except:
                result = read.split()
                for i in range(len(result)):
                    if i < len(default):
                        result[i] = self.__convert(result[i], default[i])
                    else:
                        if len(default) > 0:
                            result[i] = self.__convert(result[i], default[-1])
        elif type(default) in [dict]:
            result = eval(read, self.evalGlobals)
        else:
            result = type(default)(read)
        return result

    def __getattr__(self, name):
        if name in self.__dict__:
            return self.__dict__[ name ]
        else:
            assert self._name in self._config.sections(), "Could not find section '%s' while getting '%s'" % (self._name, name)
            activeBefore = self._config.setActiveSection(self._name)
            if not name == "defaultSections":
                for defaultSection in self.defaultSections:
                    if not self._config.get("default:%s" % defaultSection, name) == None:
                        self.setDefaults({name:self._config.get("default:%s" % defaultSection, name)})
            #self._defaults.update( eval(self._config.get(self._name, "defaults", default = "{}") ) )
            default = None
            if name in self._defaults: default = self._defaults[name]
            result = self._config.get(self._name, name, default=default)

            if type(result) == type(""):
                if not name in self._defaults or self._defaults[name] == None:
                    pass
                else:
                    result = self.__convert(result, self._defaults[name])
            self._config.setActiveSection(activeBefore)
            return result

    def setOption(self, name, value):
            assert self._name in self._config.sections(), "Could not find section '%s' while getting '%s'" % (self._name, name)
            self._config.set(self._name, name, value)

def orderByExpressions(input, expressions, sortFkt=sorted):
    from re import match
    result = []
    for orderExpr in expressions:
        for element in input:
            expr = orderExpr
            if not "$" in orderExpr:
                expr += "$"
            if not match(expr, element) == None:
                result.append(element)
    for element in sortFkt(input):
        if not element in result:
            result.append(element)
    #print list(input),"->",result
    return result


class TableEntry(object):
    template = { 0.1: "$%(value).1f \pm %(error).1f$",
                 0.01: "$%(value).2f \pm %(error).2f$",
                 - 1: " -- ",
                }
    dataTemplate = "$%(value)i$"
    #tooSmallValue = 0.1
    limitTemplate = {0.1:"$< %(limit).1f$",
                     0.01:"$< %(limit).2f$",
                     - 1: "$< 0.01$",
                     }

    sysErrorTemplate = {0.1:"$ \\pm %.1f$",
                        - 1:"$ \\pm %.2f$",
                     }


    def __init__(self, src=None, useEffective=True, isData=False, scale=0.0):
        self.isData = isData
        self.isPrediction = not isData
        self.sysErrors = {}
        self.entries = []
        self.scales = []
        if src == None:
            pass
        elif "GetEntries" in dir(src) and "GetEffectiveEntries" in dir(src) and "Integral" in dir(src):
            entries = src.GetEntries()
            if useEffective: entries = src.GetEffectiveEntries()
            self.entries = [entries]
            self.scales = [src.Integral() / self.entries[0] if self.entries[0] != 0 else scale]
        elif len(src) == 2:
            self.entries = [src[0]]
            self.scales = [src[1] if src[0] != 0 else scale]

    @property
    def value(self):
        result = 0.
        result += sum([ e * s for e, s in zip(self.entries, self.scales)])
        return result

    @property
    def error(self):
        from math import sqrt
        result = 0.
        result += sqrt(sum([ e * s * s for e, s in zip(self.entries, self.scales)]))
        #this supposes that the error is sqrt(entries)*scale
        return result

    @property
    def limit(self):
        #result = 0
        for entries, scale in zip(self.entries, self.scales):
            assert entries == 0, "all entries must be 0 to calculate limit (for now) is: '%s'" % self.entries
            assert scale > 0, "all scales must be >0 (give scale when building the TableEntry) is: '%s')" % self.scale
        result = 1.1 * max(self.scales)
        assert result > 0, "limit =0 for entries:'%s' scales:'%s'" % (self.entries, self.scales)
        return result

    @property
    def maxRelSysErrors(self):
        from math import fabs
        result = {}
        for sysErrorName, sysErr in self.sysErrors.items():
            result[sysErrorName] = max([fabs(self.value - sysErr[i].value) * 1. / self.value if self.value != 0 else 0.0  for i in range(2) ])
        return result

    def __iadd__(self, y):
        self = y + self
        return self

    def __radd__(self, y):
        if y == 0:
            return self
        else:
            return self +y

    def __add__(self, y):
        assert self.isData == y.isData, "trying to combine data with mc!"
        result = TableEntry(isData=self.isData)
        result.entries.extend(self.entries + y.entries)
        result.scales.extend(self.scales + y.scales)
        for name in self.sysErrors:
            result.sysErrors[name] = [self.sysErrors[name][i] + y.sysErrors[name][i] if len(y.entries) > 0 else self.sysErrors[name][i] for i in range(2)]
        return result

    def addSystematic(self, name, biased):
        self.sysErrors[name] = max([abs(self.value - i.value) for i in biased])

    def withRelSysError(self, relSysErrors):
        sysErrors = {}
        if relSysErrors == None:
            sysErrors = None
        else:
            for errName, errValue in relSysErrors.items():
                sysErrors[errName] = self.value * errValue
        return self.withSysError(sysErrors)

    def withSysError(self, sysErrors=None):
        result = str(self)
        if not sysErrors == None and sum(self.entries) != 0:
            result = "$".join(result.split("$")[1:-1])
            #result += "_{stat.} "
            for name, err in sysErrors.items():
                #maxTemplate = max( [i for i in self.sysErrorTemplate.keys() if i <= err])                
                #result += self.sysErrorTemplate[-1]%err #
                if err > 0.09:
                    result += "\\pm %.1f" % (err)
                else:
                    result += "\\pm %.2f" % (err)
                #result += "\\pm %.1f_{%s}"%(err, name)
            result = "$%s$" % result
        return result

    def __str__(self):
        repMap = {
                  "value": self.value,
                  "error": self.error
                  }
        if self.isData and not self.isPrediction:
            if self.value % 1 > 1e-6: print "WARNING: Data TableValue with non integer value: '%s'" % self.value
            result = self.dataTemplate % repMap
        else:
            maxTemplate = max([i for i in self.template.keys() if i <= repMap["value"]])
            result = self.template[maxTemplate] % repMap

            if repMap["value"] == 0 and not sum([abs(i) for i in self.scales]) == 0:
                repMap["limit"] = self.limit
            #if ("limit" not in repMap and repMap["value"] < self.tooSmallValue) or\
            #        ("limit" in repMap and repMap["limit"] < self.tooSmallValue):
                #repMap["limit"] = self.tooSmallValue
            #    pass
            if "limit" in repMap:
                maxTemplate = max([i for i in self.limitTemplate.keys() if i <= repMap["limit"]])
                #maxtemplate = 0.01
                result = self.limitTemplate[maxTemplate] % repMap
        return result

    def fraction(self, denom, factor=100., diffToOne=False):
        from math import sqrt
        repMap = {}

        if denom.value == 0.0: result = "N/A"
        else:
            repMap["value"] = self.value * 1. / denom.value * factor
            repMap["error"] = sqrt((1. / denom.value * self.error) ** 2 + (self.value * (1. / denom.value ** 2) * denom.error) ** 2) * factor
            if diffToOne: repMap["value"] = factor - repMap["value"]
            result = self.template % repMap
        return result

    def setSysError(self, name, up, down):
        self.sysErrors[name] = [up, down]

def parsePSet(path):
  try:
      import external.confScripts.cmsDummies as cmsDummies
  except ImportError:
      import cmsDummies
  if path == None: return None
  result = {}
  file = open(path, "r")
  rawPSets = file.read()
  file.close()
  execGlobals = {"cms":cmsDummies}
  exec(rawPSets, execGlobals)
  for psetName in filter(lambda x: x not in ["cms", "__builtins__"], execGlobals.keys()):
    if "Center" in psetName:
      result["name"] = psetName.split("Center")[0]
      result["center"] = execGlobals[psetName]
    if "Lower" in psetName:
      result["lower"] = execGlobals[psetName]
    if "Upper" in psetName:
      result["upper"] = execGlobals[psetName]
  return result

def getDileptonTrees(path, producerName, objectNames=["ETau", "MuTau", "TauTau"]):
    from ROOT import TChain
    result = {}
    for objectName in objectNames:
        result[objectName] = TChain("%sDileptonTree" % objectName)

    for name, chain in result.items():
        chain.Add("%s/%s/%sDileptonTree" % (path, producerName, name))
    return result

def printCanvas(canv, name, config, exts=["png", "pdf", "root"]):
    name = name.replace("/", "_over_")
    name = name.replace("()", "")
    name = name.replace(" ", "_")
    for ext in exts:
        figureDir = config.get("general", "figureDir")
        canv.Print("%s/%s.%s" % (figureDir, name, ext))

def compileLaTex(data, path):
    from subprocess import Popen, PIPE
    doctemplate = r"""
\documentclass[a4paper,11pt]{article}
\usepackage{amssymb}
\usepackage{amsmath}
\usepackage{epsfig}
\pagestyle{empty}
\textwidth 15cm
\setlength{\parindent}{0mm}
\begin{document}
%s
\end{document}
"""
    tabFile = open("/tmp/temp.tex", "w")
    tabFile.write(doctemplate % data)
    tabFile.close()
    #print doctemplate%data

    p = Popen("cd tables && latex -output-directory /tmp /tmp/temp.tex".split(), stdout=PIPE, stderr=PIPE)
    p.communicate()
    p = Popen("dvipng -T tight -x 1200 -z 9 /tmp/temp.dvi".split(), stdout=PIPE, stderr=PIPE)
    p.communicate()
    p = Popen(("mv temp1.png %s.png" % path).split(), stdout=PIPE, stderr=PIPE)
    p.communicate()



import unittest
class Test(unittest.TestCase):
    def setUp(self):
        file = open("helpers.unittest.ini", "w")
        file.write("""

[default:testBase]
a = <other|aNumber>
b = hallo

[default:testSpecial]
a = 2 
c = <other|<activeSection|name>>

[other]
default = config default
.*Match = matches
direct = direct
aNumber = 1
.*String = mit sauce  

[emptySection]
nothing = here

[test]
defaultSections = testBase
runtimeReplace = replace is: '.oO[replaceMe]Oo.'
sectionReplace = direct:'<other|direct>' default:'<other|triggerDefault>' match:'<other|triggerMatch>'
basicStuff = some things 
number = 1
floatNumber = 1.1
floatList = [1.1, 2.3]

[test2]
defaultSections = testBase testSpecial
name = someString

""")
        file.close()
        self.cfg = BetterConfigParser()
        self.cfg.read("helpers.unittest.ini")

    def tearDown(self):
        from os import remove
        remove('helpers.unittest.ini')

    def testBasic(self):
        self.assertTrue(self.cfg.get("test", "basicStuff") == "some things")
        self.assertTrue(self.cfg.get("other", "doesItMatch", default="not used at all") == "matches")
        self.assertTrue(self.cfg.get("other", "notEvenThere", default="direct default") == "config default")
        self.assertTrue(self.cfg.get("emptySection", "notEvenThere", default="direct default") == "direct default")

    def testRuntimeReplace(self):
        self.cfg.addRuntimeReplacement("replaceMe", "replaced.")
        self.assertTrue(self.cfg.get("test", "runtimeReplace") == "replace is: 'replaced.'")

    def testSectionReplace(self):
        self.assertTrue(self.cfg.get("test", "sectionReplace") == "direct:'direct' default:'config default' match:'matches'")

    def testSection(self):
        defaults = {
                    "number":0,
                    "anotherNumber":42,
                    "floatNumber":0.,
                    "floatList":[0., ]
                    }
        sec = Section(self.cfg, "test", defaults)
        self.assertTrue(sec.number == 1 and type(sec.number) == int)
        self.assertTrue(sec.anotherNumber == 42 and type(sec.anotherNumber) == int)
        self.assertTrue(sec.floatNumber == 1.1 and type(sec.floatNumber) == float)
        self.assertTrue(sec.floatList == [1.1, 2.3])
        self.assertTrue(sec.a == "1")
        self.assertTrue(sec.b == "hallo")

        sec = Section(self.cfg, "test2", defaults)
        self.assertTrue(sec.number == 0 and type(sec.number) == int)
        self.assertTrue(sec.anotherNumber == 42 and type(sec.anotherNumber) == int)
        self.assertTrue(sec.floatNumber == 0. and type(sec.floatNumber) == float)
        self.assertTrue(sec.floatList == [0.])
        self.assertTrue(sec.a == "2")
        self.assertTrue(sec.b == "hallo")
        self.assertTrue(sec.c == "mit sauce")

