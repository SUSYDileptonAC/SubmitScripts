#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Reworked on 27.02.2019

@author: teroerde
'''
import os.path
from os import system
from CRABAPI.RawCommand import crabCommand


import sys, os

# Disable
def blockPrint():
        sys.stdout = open(os.devnull, 'w')

# Restore
def enablePrint():
        sys.stdout = sys.__stdout__

def summary( jobSummary, task ):
        totalNum = 0.0
        numStates = 0.0
        finished = 0.0
        failed = 0.0
        running = 0.0
        other = 0.0
        
        
        for state, number in jobSummary.iteritems():
                totalNum += number
                if state == "finished":
                        finished = number
                elif state == "failed":
                        failed = number
                elif state == "running":
                        running = number
                else:
                        other += number
        
        if totalNum > 0:
                status = "\033[32m{finished:>6.1f}% \033[0m{running:>6.1f}% \033[91m{failed:>6.1f}%  \033[33m{other:>6.1f}%\033[0m   / {total:>6}".format(finished=(finished/totalNum*100), 
                                                        running=(running/totalNum*100),failed=(failed/totalNum*100), other=(other/totalNum*100), total=int(totalNum))
        else:
                status = "\033[91mNO JOBS\033[0m"
        taskName = task.split("crab_")[1]
        
        output = "{}{:>50}".format(status, taskName)
        return output


def getTasks(rawDirs,doneTasks = []):
    from glob import glob
    tasks = []
    for rawDir in rawDirs:
            if "crab_" in rawDir:       
                if not rawDir in doneTasks:    
                        tasks.append(rawDir)    
    if len(tasks) == 0:
                for rawDir in rawDirs:
                        if not rawDir == "doneTasks.shelve":
                                for dir in os.listdir(rawDir):
                                        if "crab_" in rawDir:
                                                if not os.path.join(rawDir,dir) in doneTasks:
                                                        tasks.append(os.path.join(rawDir,dir))
    if len(tasks) == 0:
                for rawDir in rawDirs:
                        for rawDirLevel2 in os.listdir(rawDir):
                                if not rawDirLevel2 == "doneTasks.shelve":
                                      for dir in os.listdir(os.path.join(rawDir,rawDirLevel2)):
                                              if "crab_" in dir:
                                                if not os.path.join(rawDir,rawDirLevel2,dir) in doneTasks:
                                                      tasks.append(os.path.join(rawDir,rawDirLevel2,dir))                
    return tasks

def resubmit(opts,tasks,doneTasks=[]):
        import tqdm
        import subprocess
        
        tasksToRemove = []
        summaries = []
        for task in tqdm.tqdm(tasks, total=len(tasks), unit="task"):
                blockPrint()
                output = crabCommand('status', dir = os.path.abspath(task))                     
                enablePrint()
                summ = summary(output["jobsPerStatus"], task)
                summaries.append(summ)
                #output = subprocess.check_output("crab status %s"%(os.path.abspath(task)), shell=True)
                if output["status"] == "COMPLETED" :
                                tasksToRemove.append(task)
                                doneTasks.append(task)    
                                print "task ", task, " is done, removing"
                elif output["status"] == "SUBMITTED" or output["status"] == "FAILED":
                        if "failed" in output["jobsPerStatus"]:
                                print "try to resubmit failed jobs in %s" % task
                                blockPrint()
                                output = crabCommand('resubmit', dir = os.path.abspath(task))  
                                enablePrint()
                                #p = subprocess.Popen(["crab", "resubmit", "%s" % os.path.abspath(task)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                #out, err = p.communicate()
                elif output["status"] == "SUBMITFAILED":
                        tasksToRemove.append(task)
                        doneTasks.append(task)
                        print "Submission of task %s failed, check input files. It is removed from job sitting for now"%(task)
        for task in tasksToRemove:
                tasks.remove(task)
        print "\033[1mTasks summary:\033[0m"
        for summ in summaries:
                print summ
        return tasks, doneTasks


def main(argv=None):
    import sys
    
    from optparse import OptionParser
    import time
    import pickle, shelve
    
    if argv == None:
        argv = sys.argv[1:]
        parser = OptionParser()
        parser.add_option("-d", "--directory", dest="directory", action="append", default=[],
                              help="crab directory")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                              help="Verbose mode.")
        parser.add_option("-l", "--lumi-report", dest="lumiReport", default=None,
                              help="filename to store lumi information in")
        parser.add_option("-w", "--watch", action="store_true", dest="watch", default=False,
                              help="Watch Folder and run resubmitter every hour, for 3 days")                         

        
        (opts, args) = parser.parse_args(argv)
        
        doneTasks = []
        for dir in opts.directory:
                if os.path.isfile("%s/doneTasks.shelve"%(dir)):
                        db=shelve.open("%s/doneTasks.shelve"%(dir))
                        doneTasks = doneTasks + db["doneTasks"]
                        db.close()
                        for task in doneTasks:
                                print "task %s already done, will not be watched"%task  
        tasks = getTasks(opts.directory,doneTasks)
        
        
        if not opts.watch:
                resubmit(opts,tasks)
        else:
                while True:
                        tasks = getTasks(opts.directory,doneTasks)
                        tasks, doneTasks = resubmit(opts,tasks,doneTasks)
                        numTasksOrig = len(tasks) + len(doneTasks)
                        if tasks == []:
                                print "All done! Terminating"
                                break
                        print "%s/doneTasks.shelve"%(opts.directory)
                        db=shelve.open("%s/doneTasks.shelve"%(opts.directory[0]))
                        db["doneTasks"]= doneTasks
                        db.close()                              
                        print "spleeping for half an hour"
                        print "sitting jobs in directory %s, %d/%d tasks done"%(opts.directory,len(doneTasks), numTasksOrig)
                        print "if you want to terminate me, now would be the right time"
                        time.sleep(1800)
                        
if __name__ == '__main__':
    main()
