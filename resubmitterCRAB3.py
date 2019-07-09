#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Reworked on 27.02.2019

@author: teroerde
'''

# do 'pip install --user tqdm' before running this if not already done
#

import os.path
from os import system
from CRABAPI.RawCommand import crabCommand
import CRABClient.ClientExceptions
from httplib import HTTPException
from datetime import datetime
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
        
        output = "{}{:>70}".format(status, taskName)
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

def kill(opts, tasks, doneTasks=[]):
        import tqdm
        import subprocess
        tasksToRemove = []
        for task in tqdm.tqdm(tasks, total=len(tasks), unit="task"):
                try:
                        output = crabCommand('kill', dir = os.path.abspath(task))                     
                except HTTPException as e:
                        print e
                tasksToRemove.append(task)
                doneTasks.append(task)
        for task in tasksToRemove:
                tasks.remove(task)
        return tasks, doneTasks
        
        
def resubmit(opts,tasks,doneTasks=[]):
        import tqdm
        import subprocess
        
        tasksToRemove = []
        summaries = []
        
        def getTaskName(task):
                return task.split("crab_")[1]
        tasks.sort(key=getTaskName)
        canStatus = True
        ex = None
        for task in tqdm.tqdm(tasks, total=len(tasks), unit="task"):
                blockPrint()  
                try:
                        output = crabCommand('status', dir = os.path.abspath(task))                     
                except HTTPException as e: # might be because of servers being down
                        canStatus = False
                        ex = e
                except CRABClient.ClientExceptions.CachefileNotFoundException:
                        enablePrint()
                        print "Removing %s because it could not be submitted"%(task)
                        tasksToRemove.append(task)
                        doneTasks.append(task)
                        continue
                finally:
                        enablePrint()
                if not canStatus:
                        print "Encountered HTTPException while getting status, will stop and wait: %s"%(str(ex))
                        break
                summ = summary(output["jobsPerStatus"], task)
                summaries.append(summ)
                if output["status"] == "COMPLETED" :
                                tasksToRemove.append(task)
                                doneTasks.append(task)    
                                print "task ", task, " is done, removing from sitting and purging from crab cache."
                                try:
                                        output = crabCommand('purge', dir = os.path.abspath(task), cache=True)  
                                except:
                                        pass
                elif output["status"] == "SUBMITTED" or output["status"] == "FAILED":
                        if "failed" in output["jobsPerStatus"]:
                                if "NEW" in output["dbStatus"] or "QUEUED" in output["dbStatus"]: # can't resubmit if job is in this state
                                        print "Task ", task, " is ", output["dbStatus"],", so jobs cannot be resubmitted now."
                                        continue
                                print "Trying to resubmit failed jobs in %s" % task
                                blockPrint()
                                couldResubmit = True
                                try:
                                        output = crabCommand('resubmit', dir = os.path.abspath(task))  
                                except CRABClient.ClientExceptions.ConfigurationException: # tasks that were marked as failed couldn't be resubmitted,
                                                                                           # usually happens if pilot jobs from automatic splitting failed
                                        couldResubmit = False
                                except HTTPException as e: # might be because of servers being down
                                        canStatus = False
                                enablePrint()
                                if not canStatus:
                                        print "Encountered HTTPException while resubmitting, will stop and wait: %s"%(str(ex))
                                        break
                                if not couldResubmit:
                                        print "No jobs to resubmit were found in %s, the failed jobs might be pilot jobs."%task
                elif output["status"] == "SUBMITFAILED":
                        tasksToRemove.append(task)
                        doneTasks.append(task)
                        print "Submission of task %s failed, check the crab directory for errors in the log file. It is removed from job sitting for now."%(task)
        for task in tasksToRemove:
                tasks.remove(task)
        if canStatus:
                print "\033[1mTasks summary (%s):\033[0m"%(datetime.now())
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
        parser.add_option("-k", "--kill", action="store_true", dest="kill", default=False,
                              help="Kill jobs in directory")
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
                                print "Task %s is already done and will not be watched."%task  
        tasks = getTasks(opts.directory,doneTasks)
        
        
        if not opts.watch:
                if opts.kill:
                        kill(opts, tasks)
                else:
                        resubmit(opts,tasks)
        else:
                while True:
                        tasks = getTasks(opts.directory,doneTasks)
                        if opts.kill:
                                tasks, doneTasks = kill(opts, tasks, doneTasks)
                        else:
                                tasks, doneTasks = resubmit(opts,tasks,doneTasks)
                        numTasksOrig = len(tasks) + len(doneTasks)
                        if tasks == []:
                                print "All done! Terminating"
                                break
                        print "%s/doneTasks.shelve"%(opts.directory)
                        db=shelve.open("%s/doneTasks.shelve"%(opts.directory[0]))
                        db["doneTasks"]= doneTasks
                        db.close()                              
                        print "Sitting jobs in %s, %d/%d tasks are done."%(" and ".join([dr for dr in opts.directory]),len(doneTasks), numTasksOrig)
                        print "If you want to terminate me, now would be the right time."
                        print "I am sleeping for half an hour"
                        try:
                                time.sleep(1800)
                        except KeyboardInterrupt:
                                exit()
                        
if __name__ == '__main__':
    main()
