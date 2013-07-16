import os,subprocess,re,glob 

def getDBSentry(job):
	settings = MainConfig()   
	dbsjob = re.compile(job)
	f = open(settings.dbsfilepath,'r')
	for line in f:
		if dbsjob.search(line):
			return line.strip() 
