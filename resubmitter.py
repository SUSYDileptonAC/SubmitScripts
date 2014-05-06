#! /usr/bin/env python
'''
Created on 10.12.2009

@author: heron
'''
import os.path

try:
  from sqlite3 import dbapi2 as sqlite # python 2.5
except:
  try:
    from pysqlite2 import dbapi2 as sqlite
  except:
    print 'This program requires pysqlite2\n', \
          'http://initd.org/tracker/pysqlite/'
    sys.exit(1)

class job:
    def __init__(self, db, jobId):
        self.__dict__.update({"job_id":jobId})
        self.__dict__.update(self.__readTable(db, "bl_job", ["name", "closed", "submission_number", "dls_destination"],
                          "job_id=%i" % self.job_id))
        self.__dict__.update(self.__readTable(db, "bl_runningjob", ["state", "application_return_code", "wrapper_return_code", "storage", "lfn"],
                         "job_id=%(job_id)i and submission =%(submission_number)i" % self.__dict__))
        #from pprint import pprint
        #pprint(self.__dict__)

    def __readTable(self, db, name, columns, condition="1=1"):
        result = {}
        for row in db.execute("select %s from %s where %s" % (", ".join(columns), name, condition)):
            if not result == {}:
                raise StandardError, "more than one row for job_id %s and condition:\n %s\n%s" % (self.job_id, condition, row)
            for i in range(len(columns)):
                result[columns[i]] = row[i]
        return result

    def getActions(self):
        #print self.job_id, self.state
        result = {"get":False, "resubmit":-1, "forceResubmit":-1, "status":self.state == "SubSuccess"}

        result["status"] = not (self.state == "Terminated" or self.state == "Cleared")
        result["get"] = self.state == "Terminated"
        result["remove"] = []
        if (self.state == "Terminated" or self.state == "Cleared") and not (self.wrapper_return_code == 0 and self.application_return_code == 0):
          if self.wrapper_return_code == 50117:
            result["forceResubmit"] = str(self.job_id)
          else:
            result["resubmit"] = str(self.job_id)
          if self.wrapper_return_code == 60303 and self.lfn:
            for lfn in eval(self.lfn):
              if not "/copy_problem/" in lfn:
                raise StandardError, "malformed lfn: %s" % lfn
              result["remove"].append("%s/%s" % (self.storage, lfn.split("/copy_problem")[1]))
        if self.state == "Aborted":
          result["resubmit"] = str(self.job_id)
        if self.state == "SubFailed":
          result["resubmit"] = str(self.job_id)
        if self.state == "None":
          result["forceResubmit"] = str(self.job_id)
                    
        return result

    def __repr__(self):
        from pprint import pformat
        #print pformat(self.__dict__)
        return str(self.__dict__) + "\n"

def readCrabDB(path):
    if not os.path.exists(path):
        raise StrandardError, "no CrabDB at '%s'" % path

    crabDB = sqlite.connect(path)
    jobs = []
    for row in crabDB.execute("select job_id from bl_job"):
         jobs.append(job(crabDB, row[0]))
    crabDB.close()
    return jobs

def getActions(rawPath, verbous=False):
    path = rawPath
    if os.path.exists(os.path.join(path, "share", "crabDB")):
        path = os.path.join(path, "share", "crabDB")

    jobs = readCrabDB(path)
    result = {"get":False, "status":False, "resubmit":[], "forceResubmit":[], "remove":[]}
    for job in jobs:
        jobAction = job.getActions()
        if verbous:
            print job.job_id, job.state, jobAction
        result["get"] = result["get"] or jobAction["get"]
        result["status"] = result["status"] or jobAction["status"]
        if jobAction["resubmit"] > 0:
          result["resubmit"].append(jobAction["resubmit"])
        if jobAction["forceResubmit"] > 0:
          result["forceResubmit"].append(jobAction["forceResubmit"])
        if not jobAction["remove"] == []:
          result["remove"].extend(jobAction["remove"])

    return result

def getTasks(rawDirs):
    from glob import glob
    tasks = {}
    
    for rawDir in rawDirs:
        for dir in glob(rawDir):
            if os.path.exists(os.path.join(dir, "share", "crabDB")):
                tasks[dir] = getActions(os.path.join(dir, "share", "crabDB"))    
    if len(tasks) == 0:
	for rawDir in rawDirs:
		for dir in os.listdir(rawDir):
			if os.path.exists(os.path.join(rawDir,dir, "share", "crabDB")):
				tasks[os.path.join(rawDir,dir)] = getActions(os.path.join(rawDir,dir, "share", "crabDB"))
                
    return tasks

def main(argv=None):
    import sys
    from os import system
    from optparse import OptionParser
    if argv == None:
        argv = sys.argv[1:]
        parser = OptionParser()
        parser.add_option("-d", "--directory", dest="directory", action="append", default=[],
                              help="crab directory")
        parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                              help="Verbose mode.")
        parser.add_option("-n", "--dry-run", action="store_true", dest="dryrun", default=False,
                              help="Dry-run mode, no job submission.")
        parser.add_option("-l", "--lumi-report", dest="lumiReport", default=None,
                              help="filename to store lumi information in")
        parser.add_option("-s", "--sort", action="store_true", dest="sort", default=False,
                              help="Sort suggestions by type")
        parser.add_option("-g", "--get", action="store_true", dest="get", default=False,
                                                        help="execute all get and report operations")
        
        (opts, args) = parser.parse_args(argv)

        from subprocess import call
        tasks = getTasks(opts.directory)
        suggestions = []
        for task in tasks:
            if tasks[task]["status"]:
                print "getting status for %s" % task
                call(["crab -c %s -status" % os.path.abspath(task)], shell=True)
            tasks[task] = getActions(task, opts.verbose)
            if tasks[task]["get"]:
                suggestions.append("crab -c %s -get" % os.path.abspath(task))
                if opts.get and not opts.dryrun:
                  system(suggestions.pop())

            tasks[task] = getActions(task)
            if not tasks[task]["resubmit"] == []:
              suggestions.append("crab -c %s -resubmit %s" % (os.path.abspath(task), ",".join(tasks[task]["resubmit"])))
            if not tasks[task]["forceResubmit"] == []:
              suggestions.append("crab -c %s -forceResubmit %s" % (os.path.abspath(task), ",".join(tasks[task]["forceResubmit"])))
            if not tasks[task]["remove"] == []:
              suggestions.append("srmrm %s" % " ".join(tasks[task]["remove"]))
            tasks[task] = getActions(task)

            if  (not tasks[task]["status"] or not opts.lumiReport == None):
            #and not os.path.exists(os.path.join(task, "res/lumiSummary.json")):
                suggestions.append("crab -c %s -report" % (os.path.abspath(task)))
                if opts.get and not opts.dryrun:
                    system(suggestions.pop())
                #print "Task: %s, status %s" % (task, tasks[task]["status"])
            jsonPath = os.path.join(task, "res/lumiSummary.json")
            print "lumiCalc2.py -i %(json)s  -o %(task)s.cvs overview"%{"json":jsonPath, "task":os.path.split(task)[-1]}
            if not opts.lumiReport == None and os.path.exists(jsonPath):
              suggestions.append("lumiCalc2.py -i %(json)s  -o %(task)s.cvs overview"%{"json":jsonPath, "task":os.path.split(task)[-1]})
              #suggestions.append("echo '%(task)s' >> %(lumiReport)s && lumiCalc.py -c frontier://LumiProd/CMS_LUMI_PROD -i %(task)s --nowarning overview >> %(lumiReport)s" % { "task":jsonPath, "lumiReport":opts.lumiReport})
              

        if (opts.sort):
            for suggestion in suggestions:
                if (suggestion.endswith("status")):
                    print suggestion
            for suggestion in suggestions:
                if (suggestion.endswith("get")):
                    print suggestion
            for suggestion in suggestions:
                if (suggestion.endswith("resubmit")):
                    print suggestion
            for suggestion in suggestions:
                if (suggestion.endswith("forceResubmit")):
                    print suggestion
            for suggestion in suggestions:
                if (suggestion.endswith("report")):
                    print suggestion
            for suggestion in suggestions:
                if (not (suggestion.endswith("status") or suggestion.endswith("get") or suggestion.endswith("resubmit") or suggestion.endswith("forceResubmit") or suggestion.endswith("report"))):
                    print suggestion
        else:
            for suggestion in suggestions:
		if not opts.dryrun:
			call(["%s" % suggestion], shell=True)
	        else:   
                	print suggestion

if __name__ == '__main__':
    main()

#_______________ UNITTESTS________________________________________ 
import unittest
class MergeHistosTest(unittest.TestCase):

    def setUp(self):
        self.originPath = os.path.abspath(os.path.curdir)

    def tearDown(self):
        os.chdir(self.originPath)

    def testReadCrabDB(self):
        compareJob = {'job_id': 1, 'wrapper_return_code': 0, 'state': u'Cleared', 'submission_number': 2, 'closed': u'Y', 'application_return_code': 0, 'dls_destination': u"['se3.itep.ru', 'grid-srm.physik.rwth-aachen.de']", 'name': u'edelhoff_SUSY_LM0_7TeV_x82q4g_job1'}
        compareAction = {'resubmit':-1, 'get': False}
        result = readCrabDB("../unittest/crabDB")
        #print result
        resultDict = {}
        for key in compareJob.keys():
            resultDict[key] = getattr(result[0], key)
        self.__assertDict(resultDict, compareJob)
        self.__assertDict(result[0].getActions(), compareAction)

    def testActions(self):
        compare = {'get': True, 'resubmit': [12, 13, 14]}
        result = getActions("../unittest/crabDB")
        #from pprint import pprint
        #pprint(result)
        self.__assertDict(result, compare)


    def __assertDict(self, result, compare):
        for key in compare.keys():
            self.assertTrue(compare[key] == result[key], "key %s differs: \n   %s\n   %s" % (key, compare[key], result[key]))
