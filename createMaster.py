#! /usr/bin/env python
import os,shutil,ConfigParser
import src.dbsTools as dbsTools

def makeMaster( NameString , datasetlist,groups = ' PL1v6c CERN QCD'):
    config = ConfigParser.ConfigParser()
    masterfile = open('./Input/Master'+NameString+'.list','w')
    fdatasets = open(datasetlist, 'r')
    datasets = fdatasets.readlines()
    fdatasets.close()
    for i in range(0,len(datasets)):
        dataset = datasets.pop(0).strip()
        secondary = dataset.split('/')[2].split('V3_')[1].rstrip('-v12')
        job = '%s_%s_%s' %(dataset.split('/')[1],secondary,NameString)
        print dataset
        print job
        print secondary
        if not config.has_section(job):
            config.add_section(job) 
        if not config.has_option(job,'groups'):
			config.set(job,'groups',NameString+' '+secondary+groups)
        if not config.has_option(job,'status'):
            config.set(job,'status','CREATED')
        if not config.has_option(job,'CrossSection'):
            config.set(job,'CrossSection',0)
        if not config.has_option(job,'kfactor'):
            config.set(job,'kfactor',1)
        if not config.has_option(job,'numEvents'):
            config.set(job,'numEvents',dbsTools.getNumEvents(dataset))
        if not config.has_option(job,'localEvents'):
            config.set(job,'localEvents',0)
        if not config.has_option(job,'datasetpath'):
            config.set(job,'datasetpath',dataset)
        if not config.has_option(job,'localdbspath'):
            config.set(job,'localdbspath','')
    config.write(masterfile)
    masterfile.close()

makeMaster('October09','/home/home4/institut_1b/nmohr/SubmitScripts/Input/datasetsOctober09.list')
