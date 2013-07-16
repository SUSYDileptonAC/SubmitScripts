#!/usr/bin/env python

from src.messageLogger import messageLogger as log
from src.job import Job

defaultContour = {
                  "name":"defaultName",
                  "input":["contour"],
                  "forScans":["mSugraTanBeta10_DileptonEnriched"],
                  "canvas":"empty",
                  "levels": {}
                  }

class Palette:
    def __init__(self, config, sectionName):
        from array import array
        from ROOT import TColor
        self._config = config
        self._name = sectionName.split("palette:")[1]
        self._sectionName = sectionName
        self._rawPalette = []
        self._legendHists = {}
        self._legendColors = {}
        self._stops = {}

        for option in self._config.options(sectionName):
            if not option in ["granularity"]:
                assert option not in self._stops, "dublicate stop name '%s'" % option
                self._stops[option] = [ float(i) for i in self._config.get(self._sectionName, option).split()]

        self._granularity = int(self._config.get(sectionName, "granularity", default="50")) * len(self._stops)
        stops = []
        red = []
        green = []
        blue = []
        for name in sorted(self._stops.keys(), key=lambda x: self._stops[x][3]):
            r, g, b, l = self._stops[name]
            red.append(r * 1. / 255.)
            green.append(g * 1. / 255.)
            blue.append(b * 1. / 255.)
            stops.append((l - self.minStop) * 1. / self.maxStop)
            self._legendColors[name] = TColor.GetColor(red[-1], green[-1], blue[-1])
#        print stops
#        print red
#        print green
#        print blue

#        print len(self._stops), array("d", stops),
#        print array("d", red), array("d", green), array("d", blue),
#        print self._granularity
        self._baseColor = TColor.CreateGradientColorTable(len(self._stops), array("d", stops),
                                                        array("d", red), array("d", green), array("d", blue),
                                                        self._granularity)

        assert self._baseColor > 0, "CreateGradientColorTable failed %s" % (self._baseColor)
        self._rawPalette = array("i", [self._baseColor + i for i in range(self._granularity)])

    @property
    def minStop(self):
        return min([ i[3] for i in self._stops.values()])

    @property
    def maxStop(self):
        return max([ i[3] for i in self._stops.values()])

    @property
    def forceRange(self):
        return False

    def activate(self):
        from ROOT import gStyle
        gStyle.SetNumberContours(self._granularity)
        gStyle.SetPalette(self._granularity, self._rawPalette)

    def drawLegend(self, xl, yl, xh, yh, header="", option="brNDC"):
        from ROOT import TLegend, TH1F
        self._legend = TLegend(*([xl, yl, xh, yh] + [header, option]))
        self._legend.SetFillColor(10)
        self._legend.SetLineColor(10)
        self._legend.SetShadowColor(0)
        self._legend.SetBorderSize(1)
        for name in self._stops:
            self._legendHists[name] = TH1F(name, name, 1, 0, 1)
            self._legendHists[name].SetFillColor(self._legendColors[name])
            self._legend.AddEntry(self._legendHists[name], name, "F")
        self._legend.Draw()



def printCanv(config, canv, name):
    from os.path import exists as pathExists
    from os import makedirs
    extensions = config.get("images", "extensions").split()

    figDir = config.get("images", "dir")
    if not pathExists(figDir):
        makedirs(figDir)

    canv.Update()
    for extension in extensions:
        canv.Print("%s/%s.%s" % (figDir, name, extension))

def makeAnnotations(annotations, size=0.04, color=1):
    from ROOT import TLatex
    latex = TLatex()
    latex.SetNDC()
    latex.SetTextSize(size)
    latex.SetTextColor(color)
    for annotation in annotations:
        assert len(annotation) == 3, "annotation has wrong length: '%s' (evalGlobal not set??)" % annotation
        latex.DrawLatex(*annotation)

def makeLimits(limits):
    from ROOT import TGraph
    from array import array
    result = []
    for limit in limits:
        repMap = { "title":"limit",
                  "drawOption":"L",
                  "lineStyle":1,
                  "lineWidth":2
                   }
        assert "x" in limit, "need 'x' got %s" % limit
        assert "y" in limit, "need 'y' got %s" % limit
        repMap.update(limit)
        x = array("f", repMap["x"])
        y = array("f", repMap["y"])
        assert len(x) == len(y), "x and y need to have same length! Got: %i != %i" % (len(x), len(y))
        graph = TGraph(len(x), x, y)
        graph.SetLineWidth(repMap["lineWidth"])
        graph.SetLineStyle(repMap["lineStyle"])
        graph.Draw("%s SAME" % repMap["drawOption"])
        result.append(graph)
    return result



def makeContours(canv, plot, contourLevels, function, text=None):
    from array import array
    from math import sqrt
    from ROOT import gROOT, TLatex, Double
    longContours = {}
    annotations = []

    plot.Draw("COLZ")
    plot.Smooth(1, "k3a")
    plot.Draw("COLZ")
    canv.Update()
    plot.SetContour(len(contourLevels), array("d", contourLevels))
    plot.Draw("CONT LIST")
    canv.Update()

    contourLists = gROOT.GetListOfSpecials().FindObject("contours")
    i = 0
    for contourList in contourLists:
        maxLen = -1
        longestGraph = None
        j = 0
        for contour in contourList:
            longContours[(i, j)] = contour.Clone()
            if maxLen < contour.GetN():
                longestGraph = contour
                maxLen = contour.GetN()
            j += 1
        #if not longestGraph == None:
        #    longContours[contourLevels[i]] = longestGraph.Clone()
        i += 1


    return (longContours, annotations)

def makePalettes(config):
    result = {"default": None}
    for sectionName in filter(lambda x: x.startswith("palette:"), config.sections()):
        palette = Palette(config, sectionName)
        result[palette._name] = palette
    return result


def drawContours(canv, section, plots):
    result = []
    for keyName, contourLevels in section.levels.items():
        result.append(makeContours(canv, plots[keyName], contourLevels, lambda n, xi, yi: n))
    return result

def plotJob(scanSection, db, propertyNames):
    from itertools import product
    from ROOT import TH2F
    result = {}
    summedChannels = {
                      "LightLeptons":["EE", "EMu", "MuMu"],
                      "Taus":["ETau", "MuTau", "TauTau"]
                      }
    log.logInfo("getting a jobs")
    numJobs = db.countJobs(scanName=scanSection.name)
    jobs = db.getJobs(scanName=scanSection.name)
    statusCounter = 0
    for job in jobs:
        x = getattr(job, scanSection.xBinColumn)
        y = getattr(job, scanSection.yBinColumn)

        for propertyName in propertyNames:
            value = getattr(job, propertyName)

            assert not value == None, "job has neither variables nor property of the name '%s'" % propertyName

            if type(value) == dict:
                for  signalRegionName, channelSumName in product(job.signalRegion, summedChannels.keys()):
                    subHistoName = "%s_%s_%s" % (propertyName, signalRegionName, channelSumName)
                    if not subHistoName in result:
                        targetName = "%s %s" % (scanSection.name, subHistoName)
                        result[subHistoName] = TH2F(targetName, targetName,
                                                    *(scanSection.xBinning + scanSection.yBinning))
                    channelSum = sum([value["%s %s" % (signalRegionName, i)] for i in summedChannels[channelSumName]])
                    if propertyName in ["genEfficiency", "pdfUncert"]:
                        channelSum = channelSum * 1. / len(summedChannels[channelSumName])
                    result[subHistoName].Fill(x, y, channelSum)
                    log.logDebug("Filling for %s at %.2f, %.2f: %.2e" % (subHistoName, x, y, channelSum))
            else:
                if not propertyName in result:
                    targetName = "%s %s" % (scanSection.name, propertyName)
                    result[propertyName] = TH2F(targetName, targetName,
                                                *(scanSection.xBinning + scanSection.yBinning))
                result[propertyName].Fill(x, y, value)
                #log.logInfo("Filling %.2f, %.2f: %.2e" % (x, y, value))
        statusCounter += 1
        log.statusBar(statusCounter, numJobs , message="Points")

    log.logInfo("Done.")
    return result


def main():
    from optparse import OptionParser
    from ROOT import TCanvas, TFile, kTRUE, kFALSE
    from src.helpers import BetterConfigParser, Section
    from src.Styles import tdrStyle
    from src.jobDB import JobDB
    from addJobs import scanDefaults

    parser = OptionParser()
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                                  help="talk about everything")
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                          help="Main configuration file. Can be given multiple times in case of split configurations. Default is jobDB.ini")
    parser.add_option("-s", "--scan", dest="scans", action="append", default=[],
                          help="names of scans to add from configuration file. Default is all found.")
    parser.add_option("-p", "--propertyNames", dest="propertyNames", action="append", default=[],
                          help="variables to plot. have to be variables or properties of Job.")
    parser.add_option("-c", "--contours", dest="contourNames", action="append", default=[],
                          help="contours to plot. have to be defined in the configuration.")

    (opts, args) = parser.parse_args()
    if (opts.verbose):
        log.outputLevel = 5
    else:
        log.outputLevel = 4

    config = BetterConfigParser()
    if opts.Config == []:
        opts.Config = ["jobDB.ini"]
    config.read(opts.Config)

    log.logInfo("Connecting to JobDB")
    db = JobDB(config, "jobDB")
    if opts.scans == []:
        opts.scans = [i.split("scan:")[1] for i in config.sections() if "scan:" in i]
        availableScans = db.getDistinct("scanName")
        opts.scans = filter(lambda x: x in availableScans, opts.scans)


    propertyNames = opts.propertyNames
    contourSections = []
    for contourName in opts.contourNames:
        contourSections.append(Section(config, "contour:%s" % contourName, defaultContour))
        propertyNames.extend(contourSections[-1].input)

    propertyNames = list(set(propertyNames))

    style = tdrStyle()
    style.SetPadRightMargin(0.25)

    palettes = makePalettes(config)

    for scanName in opts.scans:
        scanSection = Section(config, "scan:%s" % scanName, scanDefaults)
        plots = plotJob(scanSection, db, propertyNames)

        canv = TCanvas("canv", "canv", scanSection.canvasWidth, scanSection.canvasHeight)
        for plotName, plot in plots.items():
            section = "plot:%s" % plotName.split("_")[0]

            # individual plot configuration
            logZ = False
            zMin = None
            zMax = None
            zTitle = section.split(":")[-1]
            palette = None
            showLegend = False
            drawMode = "COLZ"
            if (config.has_section(section)):
                logZ = eval(config.get(section, 'logZ', default="True"))
                zMin = eval(config.get(section, 'zMin', default="None"))
                zMax = eval(config.get(section, 'zMax', default="None"))
                zTitle = config.get(section, 'zTitle', default=zTitle)
                palette = palettes[config.get(section, 'palette', default="default")]
                showLegend = eval(config.get(section, 'showLegend', default="False"))

            if (logZ):
                canv.SetLogz(kTRUE)
            else:
                canv.SetLogz(kFALSE)

            if not palette == None:
                palette.activate()
                if palette.forceRange:
                    zMin = palette.minStop
                    zMax = palette.maxStop + ((palette.maxStop - palette.minStop) * 1. / (len(palette._stops) - 1))

                if (zMin != None and zMax != None):
                    log.logWarning("Color palette set. Overwriting zMin and zMax setting")

            if showLegend:
                drawMode = "COL"
                zTitle = ""

            frame = canv.DrawFrame(scanSection.xBinning[1], scanSection.yBinning[1], scanSection.xBinning[2], scanSection.yBinning[2],
                           "%s;%s;%s" % (scanSection.scanName, scanSection.xBinTitle, scanSection.yBinTitle))
            frame.GetXaxis().SetNdivisions(9, 10, 1)
            plot.Draw("%s SAME" % drawMode)
            if "th2f" in config.get("images", "extensions").split():
                th2fFile = TFile("%s_%s.th2f.root" % (scanName, plotName), "RECREATE")
                plot.Write()
                th2fFile.Write()
                th2fFile.Close()

            plot.GetZaxis().SetTitle(zTitle)
            plot.GetZaxis().SetTitleOffset(1.5)

            if (zMin != None and zMax != None):
                #plot.GetZaxis().SetLimits(zMin, zMax)
                #SetRangeUser(zMin, zMax)
                plot.SetMinimum(zMin)
                plot.SetMaximum(zMax)

            canv.Update()
            if showLegend and not palette == None:
                palette.drawLegend(0.88, 0.13, 1, 0.95)

            makeAnnotations(scanSection.annotations)
            limits = makeLimits(eval(scanSection.limits))

            frame.Draw("SAME")
            printCanv(config, canv, "%s_%s_%s" % (scanName, scanSection.configTag, plotName))

        for contourSection in contourSections:
            if scanName in contourSection.forScans:
                canv = TCanvas("canv", "canv", scanSection.canvasWidth, scanSection.canvasHeight)
                canv.Draw()

                contours = drawContours(canv, contourSection, plots)


                if not contourSection.canvas == "empty":
                    canvFile = TFile(contourSection.canvas.split(":")[0], "r")
                    canv = canvFile.Get(contourSection.canvas.split(":")[1])

                i = 1
                for contourDict, annotation in contours:
                    for contourName, contour in contourDict.items():
                        contour.SetLineWidth(2)
                        contour.SetLineColor(i)
                        contour.Draw("SAME")
                    i += 1

                canv.Draw()
                printCanv(config, canv, contourSection.name)


#entry point
if (__name__ == "__main__"):
    main()


