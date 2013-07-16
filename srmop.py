import os,subprocess,glob,dbsop
import src.analysis as analysis


#FIXME these functions change the current directoy. cleanup needed.
def srmcp(pnfspfad,abspfad):
	print 'Copying ... '+pnfspfad+' to'+abspfad
	subprocess.call(['srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN='+pnfspfad+' file:///'+abspfad],shell=True)
	#subprocess.call(['srmcp -debug=true srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN='+pnfspfad+' file:///'+abspfad],shell=True)
	#print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN='+pnfspfad+' file:///'+abspfad

def srmrelcp(pnfspfad,pfad):
	print 'Copying ... '+pnfspfad+' to'+pfad
	subprocess.call(['srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN='+pnfspfad+' file:///'+pfad],shell=True)
        #print 'working directory: ' + os.getcwd()
	#print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN='+pnfspfad+' file:///'+pfad

def srmdel(pnfspfad):
	print 'Deleting ... '+pnfspfad
	subprocess.call(['srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN='+pnfspfad],shell=True)
        #print 'working directory: ' + os.getcwd()

def DeleteAll(job):
	#delete the DBS entry
	if cfg.has_option(job,'localdbspath'):
		subprocess.call(['${CRABDIR}/python/DBSDeleteData.py --DBSURL='+dbsurl+' --datasetPath='+cfg.get(job,'localdbspath')],shell=True)
	#delete the files
	files = glob.glob('/pnfs/physik.rwth-aachen.de/cms/phedex/store/user/sprenger/*/'+job+'/*/*.root')
	for pnfsfile in files:
		srmdel(pnfsfile)
	logfiles = glob.glob('/pnfs/physik.rwth-aachen.de/cms/phedex/store/user/sprenger/*/'+job+'/*/*.log')
	for logfile in logfiles:
		srmdel(logfile)
	#subprocess.call(['srmrmdir srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN='+datapath+'/'+job],shell=True)

def CopyLogs(job):
	os.chdir(logpath)
	if not os.path.exists(job):
		os.mkdir(job)
	os.chdir(job)
	pnfslogfiles = glob.glob(datapath+'/'+job+'/'+logname+'*.log')
	for n in range(len(pnfslogfiles)):
		if not os.path.exists(os.path.basename(pnfslogfiles[n])):
			print pnfslogfiles[n]
			print os.path.basename(pnfslogfiles[n])
			srmrelcp(pnfslogfiles[n],os.path.basename(pnfslogfiles[n]))
			if os.path.exists(os.path.basename(pnfslogfiles[n])):
				srmdel(pnfslogfiles[n])
def CopyLogsDBS(job):
	if dbsop.getDBSentry(job):
		os.chdir(logpath)
		if not os.path.exists(job):
			os.mkdir(job)
		os.chdir(job)
		pnfslogfiles = glob.glob('/pnfs/physik.rwth-aachen.de/cms/phedex/store/user/sprenger/*/'+job+'/*/'+logname+'*.log')
		for n in range(len(pnfslogfiles)):
			if not os.path.exists(os.path.basename(pnfslogfiles[n])):
				print pnfslogfiles[n]
				print os.path.basename(pnfslogfiles[n])
				srmrelcp(pnfslogfiles[n],os.path.basename(pnfslogfiles[n]))

def myls(pfad):
	commander = 'lcg-ls srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN='+pfad
	lcgls = subprocess.Popen(commander, shell=True, stdout=subprocess.PIPE).stdout
	print lcgls

def CopyLogsDBS1(job,pfad,n=1):
	os.chdir(logpath)
	if not os.path.exists(job):
		os.mkdir(job)
	os.chdir(job)
	for i in range(1,n+1):
		srmrelcp(pfad+'/skimming_'+str(i)+'.log','skimming_'+str(i)+'.log')

def CopyHistos1(job,flag,task,n=1):
	if job=='WJets_madgraph_Fall08':
		n=3
	for i in range(1,n+1):
		srmcp(storagepath+'/data/Histos/'+job+'/'+flag+'.'+task+'.'+job+'_'+str(i)+'.root',analysispath+ '/Histos/'+flag+'.'+task+'.'+job+'_'+str(i)+'.root')
		if os.path.exists(analysispath+ '/Histos/'+flag+'.'+task+'.'+job+'_'+str(i)+'.root'):
			srmdel(storagepath+'/data/Histos/'+job+'/'+flag+'.'+task+'.'+job+'_'+str(i)+'.root')
		srmcp(storagepath+'/data/Histos/'+job+'/'+flag+'_'+task+'_'+job+'_'+str(i)+'.log',analogpath+'/'+flag+'_'+task+'_'+job+'_'+str(i)+'.log')
		if os.path.exists(analogpath+ '/'+flag+'_'+task+'_'+job+'_'+str(i)+'.log'):
			srmdel(storagepath+'/data/Histos/'+job+'/'+flag+'_'+task+'_'+job+'_'+str(i)+'.log')
	

def CopyHistos(job):
	os.chdir(analysispath+'/Histos')
	pnfsfiles = glob.glob(storagepath+'/data/Histos/'+job+'/*.root')
	for n in range(len(pnfsfiles)):
		print pnfsfiles[n]
		print os.path.basename(pnfsfiles[n])
		#srmrelcp(pnfsfiles[n],os.path.basename(pnfsfiles[n]))
                srmcp(pnfsfiles[n], analysispath + '/Histos/' + os.path.basename(pnfsfiles[n]))
		if os.path.exists(analysispath + '/Histos/' + os.path.basename(pnfsfiles[n])):
			srmdel(pnfsfiles[n])
			#print 'File deleted'
		#else:
			#print 'Copying failed, not deleting file'
        os.chdir(analogpath)
	pnfslogfiles = glob.glob(storagepath+'/data/Histos/'+job+'/*.log')
	for n in range(len(pnfslogfiles)):
		print pnfslogfiles[n]
		print os.path.basename(pnfslogfiles[n])
		#srmrelcp(pnfslogfiles[n],os.path.basename(pnfslogfiles[n]))
		srmcp(pnfslogfiles[n], analogpath + "/" + os.path.basename(pnfslogfiles[n]))
		if os.path.exists(analogpath + "/" + os.path.basename(pnfslogfiles[n])):
			srmdel(pnfslogfiles[n])
			#print 'File deleted'
		#else:
			#print 'Copying failed, not deleting file'

def CopyData(job):
	os.chdir(localdatapath)
	if not os.path.exists(job):
		os.mkdir(job)
	files = glob.glob(datapath+'/'+job+'/'+filename+'*.root')
	for pnfsfile in files:
                number = analysis.getNumberRoot(pnfsfile)
                if not os.path.exists(localdatapath+'/'+job+'/'+filename+number+'.root'):
			srmcp(pnfsfile,localdatapath+'/'+job+'/'+filename+number+'.root')
			print filename+number+'.root'
