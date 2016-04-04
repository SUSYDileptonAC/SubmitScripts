#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Created on 10.12.2009

@author: heron
'''
import os.path
from os import system




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

	import subprocess
	tasksToRemove = []
        for task in tasks:
                print "try to resubmit failed jobs in %s" % task
                p = subprocess.Popen(["crab", "resubmit", "%s" % os.path.abspath(task)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                out, err = p.communicate()
        
		if "resubmission process proceed" in out:
		    print "succesfully resubmitted jobs"
		elif "['failed']" in out:
		    print "no jobs to resubmit at the moment"
		elif "COMPLETED" in out:
		    print "task done, add to list of tasks to be removed"
		    tasksToRemove.append(task)
		    doneTasks.append(task)
        
	for task in tasksToRemove:
		print "task ", task, " is done, removing"
		tasks.remove(task)
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
				print "task %s already done, will not be wachted"%task	
        tasks = getTasks(opts.directory,doneTasks)
	
	numTasksOrig = len(tasks) + len(doneTasks)
  	if not opts.watch:
		resubmit(opts,tasks)
	else:
		while True:
			tasks = getTasks(opts.directory,doneTasks)
			tasks, doneTasks = resubmit(opts,tasks,doneTasks)
			if tasks == []:
				print "All done! Terminating"
				break
			print "%s/doneTasks.shelve"%(opts.directory)
			db=shelve.open("%s/doneTasks.shelve"%(opts.directory[0]))
			db["doneTasks"]= doneTasks
			db.close()				
			print "spleeping for half an hour"
			print "sitting jobs in directory %s, %d/%d tasks done"%(opts.directory,numTasksOrig-len(tasks), numTasksOrig)
			print "if you want to terminate me, now would be the right time"
			time.sleep(1800)
			
if __name__ == '__main__':
    main()
