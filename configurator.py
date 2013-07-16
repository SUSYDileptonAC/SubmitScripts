import os,shutil,dbsop,srmop
import src.analysis as analysis

def createJobs( settings ):
	masterfile = open('%(Input)s/Master1.list'%settings.getMap,'w')
	fjobs=open(joblist, 'r')
	fdatasets=open(datasetlist, 'r')
	jobs = fjobs.readlines()
        datasets = fdatasets.readlines()
        for i in range(0,len(jobs)):
		job=jobs.pop(0).strip()
		print job
		dataset=datasets.pop(0).strip()
		if not config.has_section(job):
	                config.add_section(job) 
		if not config.has_option(job,'datasetpath'):
			config.set(job,'datasetpath',dataset)
		if not config.has_option(job,'CrossSection'):
			config.set(job,'CrossSection',0)
		if not config.has_option(job,'kfactor'):
			config.set(job,'kfactor',1)
		if not config.has_option(job,'status'):
			config.set(job,'status',0)
	config.write(masterfile)
	shutil.move("%(Input)s/Master1.list"%settings.getMap(),master)

def updateJobs( settings ):
	masterfile = open('%(Input)s/Master1.list'%settings.getMap(),'w')
	for job in config.sections():
		if not config.has_option(job,'localDBSpath'):
			if dbsop.getDBSentry(job):
				config.set(job,'localDBSpath',dbsop.getDBSentry(job))
				#srmop.CopyLogsDBS(job)
				passedNumbers, skimNumbers = analysis.numbers(job)
				config.set(job,'NumEvents',passedNumbers)
				config.set(job,'LocalEvents',skimNumbers)
	config.write(masterfile)
	shutil.move('%(Input)s/Master1.list'%settings.getMap(), master)
	#os.chmod(homedir+'/public/Master.list',0640)
