#! /usr/bin/env python

import os,shutil,glob,re,ConfigParser,subprocess,crab,srmop,FamosMaster

homedir = os.path.expanduser('~')
master = homedir+'/SUSY/Python/Input/Scan.list'
slhapath = homedir+'/SUSYcalculation/Scan/SLHA' # need to update
famospath = homedir+'/famos/223' # need to update
pnfspath = '/pnfs/physik.rwth-aachen.de/cms/phedex/store/user/sprenger' # need to update
config = ConfigParser.ConfigParser()
config.read(master)
masterfile = open(homedir+'/SUSY/Python/Input/Scan1.list','w') # need to update

nan= re.compile('                NAN')
#xsec= re.compile('|')
xsec= re.compile(' I   0 All included subprocesses    I        10000        ')

def checkSLHA(slha):
	fslha=open(slha, 'r')
        for line in fslha:
                if nan.match(line):
			fslha.close()
			return False
	fslha.close()
	return True

def parseSLHA(slha):
	fslha = os.path.basename(slha)
	job = fslha[0:len(fslha)-5]
	piece = job[job.find('_')+1:len(job)]
	m0 = piece[0:piece.find('_')]
	piece = piece[piece.find('_')+1:len(piece)]
	m12 = piece[0:piece.find('_')]
	piece = piece[piece.find('_')+1:len(piece)]
	tanb = piece[0:piece.find('_')]
	piece = piece[piece.find('_')+1:len(piece)]
	sgnmu = piece[0:piece.find('_')]
	a0 = piece[piece.find('_')+1:len(piece)]
	return job, m0, m12, tanb, sgnmu, a0
	
def makeReady(job):
	print 'Creating crab job ...'
	if config.has_section(job):
		f=open(famospath+'/'+job+'.py', 'w')
	        f.write(FamosMaster.createCFG(job))
       		f.close()
		CMSSW = os.environ['CMSSW_BASE']
		CMSSW = CMSSW[CMSSW.rfind('/'):len(CMSSW)]
		shutil.copyfile(config.get(job,'slhafile'),homedir+CMSSW+'/src/NiklasMohr/SLHA/data/'+job+'.slha')
		crab.submitFamos(job,False,False)
		os.remove(homedir+CMSSW+'/src/NiklasMohr/SLHA/data/'+job+'.slha')
	        config.set(job,'status','0')

def submit(job):
	print 'Submitting crab job ...'
	subprocess.call(['crab -submit -c '+famospath+'/'+job],shell=True)
	config.set(job,'status','1')

def getoutput(job):
	#rootfiles = glob.glob(pnfspath+'/'+job+'/'+job+'/*/'+job+'_1.root')
	#if len(rootfiles)>0:
		#if os.path.getsize(rootfiles[0])>1000000:
			print 'Getting output of crab job ...'
			subprocess.call(['crab -status -c '+famospath+'/'+job],shell=True)
			subprocess.call(['crab -getoutput -c '+famospath+'/'+job],shell=True)
			if os.path.exists(famospath+'/'+job+'/res/CMSSW_1.stdout'):
				print 'Hi'
				config.set(job,'status','G')

def publish(job):
	print 'Publishing dataset in DBS ...'
	subprocess.call(['crab -publish -c '+famospath+'/'+job],shell=True)
	config.set(job,'status','P')

def finish(job):
	print 'Finishing everything ...'
	f=open(famospath+'/'+job+'/res/CMSSW_1.stdout','r')
	for line in f:
                if xsec.match(line):
			crossec = float(line[len(line)-12:len(line)-2])*1E9
			config.set(job,'pythia_xsec',crossec)
	f.close()
	dbsentry = re.compile('/'+job)
	fdbs=open(homedir+'/Python/Input/ScanDBS.list','r')
	for line in fdbs:
		if dbsentry.match(line):
			localdbspath = line.strip()
			config.set(job,'localdbspath',localdbspath)
	fdbs.close()
	if config.has_option(job,'pythia_xsec') and config.has_option(job,'localdbspath'):
		config.set(job,'status','F')

def createJobs():
        slhafiles = glob.glob(slhapath+'/CalibmSUGRA_*_*_10_1_m400.slha')
	for i in range(0,len(slhafiles)):
                slha=slhafiles.pop(0).strip()
		if checkSLHA(slha):
			job, m0, m12, tanb, sgnmu, a0 = parseSLHA(slha)
                	if not config.has_section(job):
                        	config.add_section(job)
             		if not config.has_option(job,'status'):
                        	config.set(job,'status','C')
                	if not config.has_option(job,'slhafile'):
                        	config.set(job,'slhafile',slha)
                	if not config.has_option(job,'m0'):
                        	config.set(job,'m0',m0)
                	if not config.has_option(job,'m12'):
                        	config.set(job,'m12',m12)
                	if not config.has_option(job,'tanb'):
                        	config.set(job,'tanb',tanb)
	                if not config.has_option(job,'sgnmu'):
                        	config.set(job,'sgnmu',sgnmu)
                	if not config.has_option(job,'a0'):
                        	config.set(job,'a0',a0)
        config.write(masterfile)
        shutil.move(homedir+'/Python/Input/Scan1.list',master)

def done():
	i = 0
	for job in config.sections():
		if config.get(job,'status') == 'F':
			i += 1
	print '\033[1;34m'+str(i)+' of '+str(len(config.sections()))+' done.\033[1;m'

def copy(job):
	rootfiles = glob.glob(pnfspath+'/'+job+'/'+job+'/*/'+job+'_1.root')
	abspath = '/disk1/user/nmohr/skimSummer08/data/'+job
	if not os.path.exists(abspath+'/skimPAT_0.root'):
		print 'Copying '+rootfiles[0]+' to '+abspath+'/skimPAT_0.root'
		if not os.path.exists(abspath):
			os.mkdir(abspath)
		srmop.srmcp(rootfiles[0],abspath+'/skimPAT_0.root')

def checkAll():
	i = 0
	jobs = config.sections()
	number = len(jobs)
	for job in jobs:
		i += 1
		print '\033[1;34m'+str(i)+' of '+str(number)+': '+job+'\033[1;m'
		if config.get(job,'status') == 'P':
			finish(job)
		if config.get(job,'status') == 'G':
			publish(job)
		if config.get(job,'status') == '1':
			getoutput(job)
		if config.get(job,'status') == '0':
			submit(job)
		if config.get(job,'status') == 'C':
			makeReady(job)
	config.write(masterfile)
	shutil.move(homedir+'/Python/Input/Scan1.list',master)
	done()

def test():
	for job in config.sections():
		if config.get(job,'status') == 'F':
			print job
			logfile = glob.glob(pnfspath+'/'+job+'/'+job+'/*/production_1.log')
			print logfile[0]
			#print config.get(job,'status')

def analysis(flag,task,mode='v'):
	i = 0
	jobs = config.sections()
	number = len(jobs)
	for job in jobs:
		i += 1
		print '\033[1;34m'+str(i)+' of '+str(number)+': '+job+'\033[1;m'
		if (i >= 110):
			if config.get(job,'status') == 'F':
				if not os.path.exists('/home/home4/institut_1b/sprenger/SUSY/PAT/Histos/'+flag+'.'+task+'.'+job+'.root'):
					subprocess.call(['./run.py -'+mode+' -f '+flag+' -t '+task+' -j '+job],shell=True)

#makeReady('mSUGRA_1600_900_10_1_0')
#createJobs()
#copy('mSUGRA_1600_750_10_1_0')
#checkAll()
#analysis('MVA','LM1_1_bdt7p25Trees20Pruning','vM')
#analysis('MVA','LM9t175_1_bdt7p150Trees25Pruning','vM')
#analysis('Run3','3JetmediumMET','vg')
analysis('sw229v0102','commonJetCuts2SSLeptons','vg')
#test()
