#=======================================================
# Project: LocalAnalysis
#              SUSY Same Sign Dilepton Analysis
#
# File: messageLogger.py
#
# Author: Daniel Sprenger
#         daniel.sprenger@cern.ch
#=======================================================

class messageLogger(object):
    '''
    classdocs
    '''
    outputLevel = 5 # print all log messages
    warningCounter = 0
    errorCounter = 0
    lastStatusCounter = 0
    startTime = None


    def __init__(self):
        '''
        Constructor
        '''

    @staticmethod
    def __log(message, priority):
        if (messageLogger.outputLevel >= priority):
            print message
        return

    @classmethod
    def logDebug(cls, message):
        cls.__log(message, 5)
        return

    @classmethod
    def logInfo(cls, message):
        cls.__log(message, 4)
        return

    @classmethod
    def logHighlighted(cls, message):
        cls.__log("\033[1;34mInfo: " + message + "\033[0m", 3)
        return

    @classmethod
    def logWarning(cls, message):
        cls.__log("\033[1;33mWarning: " + message + "\033[0m", 2)
        cls.warningCounter += 1
        return

    @classmethod
    def logError(cls, message):
        cls.__log("\033[1;31mError: " + message + "\033[0m", 1)
        cls.errorCounter += 1
        return

    @classmethod
    def logZimLink(cls, path, width=400):
        cls.logHighlighted("Zim link to plot:\n{{file://%s?width=%d}}" % (path, width))
        return

    @classmethod
    def logOpenCommand(cls, path):
        cls.logInfo("Command to open plot:\nopen /%s" % (path))
        return

    @classmethod
    def printSummary(cls):
        if (cls.warningCounter > 0):
            cls.__log("\033[1;34mSummary: There have been \033[1;33m%d warnings!\033[1;m" % cls.warningCounter, 2)
        if (cls.errorCounter > 0):
            cls.__log("\033[1;34mSummary: There have been \033[1;31m%d errors!\033[1;m" % cls.errorCounter, 1)

    @classmethod
    def statusBar(cls, current, all, stepsShown=60, message="Status"):
        import sys
        from time import time
        fraction = current * 1. / all
        if cls.lastStatusCounter == 0 or (current - cls.lastStatusCounter) * 1. / all > 0.001:
            cls.lastStatusCounter = current
            if cls.startTime == None:
                cls.startTime = time()
            eta = (time() - cls.startTime) * (1. - fraction) * 1. / fraction if fraction > 0 else 0.
            sys.stdout.write("\r\033[1;33m%s: [%s] %.1f %% (ETA %.1f s)\033[m" % (message, (int(stepsShown * fraction) - 1) * "=" + ">" + int(stepsShown * (1 - fraction)) * " ", 100.*fraction, eta))
            sys.stdout.flush()
        if current >= all:
            cls.lastStatusCounter = 0
            sys.stdout.write("\n")
            cls.startTime = None
            sys.stdout.flush()





