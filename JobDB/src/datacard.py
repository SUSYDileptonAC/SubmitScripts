#!/usr/bin/env VERSIONER_PYTHON_PREFER_32_BIT=yes python

#=======================================================
# File: makeDatacard.py
#
# Author: Daniel Sprenger
#         daniel.sprenger@cern.ch
#=======================================================

from messageLogger import messageLogger as log

from ConfigParser import SafeConfigParser
import os

class DataCard(object):
    # templates
    block1 = """# Counting experiment with multiple channels
imax %(nChannels)d  number of channels
jmax *  number of backgrounds ('*' = automatic)
kmax *  number of nuisance parameters (sources of systematical uncertainties)
"""

    block2 = """# three channels, each with it's number of observed events 
bin          %(listChannels)s
observation   %(listObservations)s     
"""

    block3 = """# now we list the expected events for signal and all backgrounds in those three bins
# the second 'process' line must have a positive number for backgrounds, and 0 for signal
# for the signal, we normalize the yields to an hypothetical cross section of 1/fb
# so that we get an absolute limit on xsec times BR times Acceptance.
# then we list the independent sources of uncertainties, and give their effect (syst. error)
# on each process and bin
bin         %(listBins)s
process   %(listProcesses)s
process    %(listProcessNumbers)s
rate       %(listProcessRates)s
"""

    # just an example
    # will be generated automatically
    block4 = """lumi    lnN   1.06   -     1.06   -         1.06    -       1.06   -       1.06    -        1.06    -     A 6% lumi uncertainty, affects signal and MC-driven background
ZtoTau  lnN   -      -     1.50   -         -       -       1.50   -       -       -        1.50    -     A 50% uncertainty on z to taus
tauId   lnN   1.10   1.10  1.10   -         1.10    1.10    1.10   -       1.20    1.20     1.20    -     A 10% tauId uncertainty
eleId   lnN   1.02   1.02  1.02   -         -       -       -      -       -       -        -       -     A 2% eleId uncertainty
muId    lnN   -      -     -      -         1.02    1.02    1.02   -       -       -        -       -     A 2% muId uncertainty
jes     lnN   1.07   -     -      -         1.07    -       -      -       1.07    -        -       -     A 5% JES affects signal
top     lnN   -      1.30  -      -         -       1.30    -      -       -       1.30     -       -     A 30% top uncertainty from ptll
Fake    lnN   -      -     -      1.50       -       -       -      1.50    -      -        -       1.50  A 15% fake uncertainty from TL (dominated by stats)
"""

    separator = """------------
"""

    def makeDataCard(self, configParser, name):
        #cfgBase, cfgExt = os.path.splitext(cfg)
        #filename = "%s_datacard.txt" % (cfgBase)
        filename = "%s_datacard.txt" % (name)
        log.logInfo("writing datacard: %s" % (filename))
        file = open(filename, 'w')

        dict = self.prepareDict(configParser)

        log.logDebug("writing block 1")
        file.write(DataCard.block1 % dict)
        file.write(DataCard.separator)
        log.logDebug("writing block 2")
        file.write(DataCard.block2 % dict)
        file.write(DataCard.separator)
        log.logDebug("writing block 3")
        file.write(DataCard.block3 % dict)
        file.write(DataCard.separator)
        log.logDebug("writing block 4")

        for key in dict['listCorrelations'].keys():
            file.write("%s \n" % (dict['listCorrelations'][key]))
        #file.write(block4)

        file.close()
        return

    makeDataCard = classmethod(makeDataCard)


    def prepareDict(self, parser):
        #parser = SafeConfigParser()
        #parser.read(cfg)

        channels = [section for section in parser.sections() if section.startswith("channel:")]
        listChannels = ""
        listObservations = ""
        listProcesses = ""
        listProcessNumbers = ""
        listProcessRates = ""
        listBins = ""

        uncertainties = [section for section in parser.sections() if section.startswith("uncertainty:")]
        uncertaintyDescriptions = [parser.get(uncertainty, "description") for uncertainty in uncertainties]
        correlations = {}
        listCorrelations = {}

        for uncertainty in uncertainties:
            listCorrelations.update({uncertainty: "%s   lnN " % uncertainty.replace("uncertainty:", "")})

        log.logDebug("uncertainties: %s" % uncertainties)
        for uncertainty in uncertainties:
            tempUncertainty = {}
            correlatedchannels = [option for option in parser.options(uncertainty) if (option.startswith("processes_"))]
            for correlatedchannel in correlatedchannels:
                temp = {}
                correlatedprocesses = eval(parser.get(uncertainty, correlatedchannel))
                correlationvalues = eval(parser.get(uncertainty, correlatedchannel.replace("processes_", "correlations_")))
                for iProcess in range(0, len(correlatedprocesses)):
                    temp.update({correlatedprocesses[iProcess].lower(): correlationvalues[iProcess]})

                tempUncertainty.update({correlatedchannel.replace("processes_", ""): temp})
            correlations.update({uncertainty.replace("uncertainty:", ""): tempUncertainty})
        log.logDebug("correlations: %s" % correlations)


        for channel in channels:
            listChannels += " %s" % channel.replace("channel:", "")
            #log.logDebug("Observation: %s" % parser.get(channel, "observation"))
            listObservations += "   %d" % (parser.getint(channel, "observation"))

            processes = [option for option in parser.options(channel) if (option.startswith("process_") and option.endswith("_rate"))]

            # sort susy to the front (signal has to have id 0)
            signalProcessName = "process_susy_rate"
            if (signalProcessName in processes):
                processes.remove(signalProcessName)
                rest = [process for process in processes]
                processes = [signalProcessName]
                processes.extend(rest)

            log.logDebug("processes: %s" % processes)
            processNumber = 0
            for process in processes:
                listProcesses += "    %s" % (process.replace("process_", "").replace("_rate", ""))
                listProcessNumbers += "      %d" % processNumber
                log.logDebug("%s rate: %s" % (process, parser.get(channel, process)))
                listProcessRates += "    %s" % eval(parser.get(channel, process))
                #listProcessRates += "    %s" % (parser.getfloat(channel, process))
                listBins += "  %s" % channel.replace("channel:", "")

                for uncertainty in uncertainties:
                    uncertaintyName = uncertainty.replace("uncertainty:", "")
                    channelName = channel.replace("channel:", "")
                    processName = process.replace("process_", "").replace("_rate", "")
                    #log.logDebug("%s" % correlations)
                    #log.logDebug("%s - %s - %s" % (channelName, processName, uncertainty))
                    if (correlations.has_key(uncertaintyName)
                        and correlations[uncertaintyName].has_key(channelName)
                        and correlations[uncertaintyName][channelName].has_key(processName)):
                        listCorrelations.update({uncertainty: "%s   %.3f" % (listCorrelations[uncertainty], correlations[uncertaintyName][channelName][processName])})
                    else:
                        listCorrelations.update({uncertainty: "%s     - " % (listCorrelations[uncertainty])})
                    pass

                processNumber += 1
                pass


        for iUncertainty in range(0, len(uncertainties)):
            listCorrelations.update({uncertainties[iUncertainty]: "%s   %s" % (listCorrelations[uncertainties[iUncertainty]], uncertaintyDescriptions[iUncertainty])})

        log.logDebug("channels: %s (%d)" % (channels, len(channels)))

        dict = {
            'nChannels': len(channels),
            'listChannels': listChannels,
            'listObservations': listObservations,
            'listBins': listBins,
            'listProcesses': listProcesses,
            'listProcessNumbers': listProcessNumbers,
            'listProcessRates': listProcessRates,
            'listCorrelations': listCorrelations,
            }
        return dict


    prepareDict = classmethod(prepareDict)
