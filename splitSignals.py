import argparse
import os
import shutil
import glob
import multiprocessing as mp
import subprocess as sp


def split_samples(config):
    cmd = ("python treePostprocessorSignal.py -C %s"%(config)).split(" ")

    sp.call(cmd)
    #p = sp.Popen(cmd, shell=True, stdout=subprocess.STDOUT, stderr=subprocess.STDOUT)
    #try:
        #p.wait()
    #except KeyboardInterrupt:
        #try:
           #p.terminate()
        #except OSError:
           #pass
        #p.wait()


def main():
    parser = argparse.ArgumentParser(description='Ini file generator')
    parser.add_argument("-C", "--Config",action="store", dest="config", default="Input/default102X.ini",
                                              help="For which year?")
    parser.add_argument("-y", "--year",action="store", dest="year", default="2017",
                                              help="For which year?")
    parser.add_argument("-s", "--sample",action="store", dest="sample", default="T6bbllslepton",
                                              help="Which sample to split?")
    parser.add_argument("-n", "--ncores",action="store", dest="ncores", default=1, type=int,
                                              help="How many parallel processes?")
    parser.add_argument("-m", "--move",action="store_true", dest="move", default=False,
                                              help="Move samples from merged histos folder?")
    parser.add_argument("-r", "--remove",action="store_true", dest="remove", default=False,
                                              help="Remove old cleaning samples?")
    parser.add_argument("-f", "--flag",action="store", dest="flag", default=None,
                                              help="Sample flag")
    args = parser.parse_args()
    
    import src.mainConfig
    settings = src.mainConfig.MainConfig([args.config,])
    print settings.mergedhistopath
    
    if args.flag == None:
        print "No flag given, exiting"
        exit()
    
    if args.year == "2017":
        yearAppend = "Fall17"
    elif args.year == "2016":
        yearAppend = "Summer16"
    elif args.year == "2018":
        yearAppend = "Autumn18"
    
    masses = []
    if args.sample == "T6bbllslepton":
        masses = ["msbottom_400To775_GeV", "msbottom_800To1375_GeV", "msbottom_1400To1800_GeV"]
        renameName = "T6bbllslepton_msbottom_{mQ}_mneutralino_{mN}"
    elif args.sample == "T6qqllslepton":
        masses = ["msquark_1000To2100_GeV",]
        renameName = "T6qqllslepton_msquark_{mQ}_mneutralino_{mN}"
    
    task = "cuts{year}DileptonSignal".format(year=args.year)
    
    # move files in place for splitting
    if args.move:
        srcFolder = os.path.join(settings.mergedhistopath, args.flag,task)
        print "moving from", srcFolder
        # first ensure that old files are removed if new ones are moved in
        if args.remove:
            for massRange in masses:
                destFolder = "{cleaningPath}/Signals/{sample}/{massRange}".format(cleaningPath=settings.cleaningpath,sample=args.sample, massRange=massRange)
                if not os.path.isdir(destFolder):
                    os.makedirs(destFolder)
                filesToRemove = glob.glob(destFolder+"/*.root")
                for fi in filesToRemove:
                    print "removing", os.path.join(fi)
                    os.remove(os.path.join(destFolder,fi))
            
        for massRange in masses:
            destFolder = "{cleaningPath}/Signals/{sample}/{massRange}".format(cleaningPath=settings.cleaningpath,sample=args.sample, massRange=massRange)
            fileName = "{flag}.{task}.{sample}_{massRange}_{yearAppend}.root".format(flag=args.flag, task=task, sample=args.sample, massRange=massRange, yearAppend=yearAppend)
            print "putting", os.path.join(destFolder, fileName)
            shutil.move(os.path.join(srcFolder, fileName), os.path.join(destFolder, fileName))
            
    # split signals
    
    cfgFolder = "CfgMerge/mergeSystematics/{year}/{sample}".format(year=args.year, sample=args.sample)
    configs = glob.glob(cfgFolder+"/*.ini")
    pool = mp.Pool(processes=args.ncores)
    pool.map_async(split_samples, configs)
    pool.close()
    pool.join()
    print "Done splitting, renaming now"
    # rename signals
    
    folderNames = glob.glob("{procPath}/Signals/{sample}/*".format(procPath=settings.processedpath, sample=args.sample))
    
    for folder in folderNames:
        massQ = folder.split("/")[-1].split("_")[2]
        massN = folder.split("/")[-1].split("_")[5]
        fileName = glob.glob("{folder}/*.root".format(folder=folder))[0]
        fileNew = "{flag}.{task}.{rename}_{yearAppend}.root".format(flag=args.flag, task=task, sample=args.sample, rename=renameName.format(mQ=massQ, mN=massN), yearAppend=yearAppend)
        destDir = os.path.join(settings.treespath, "{}_{}".format(args.flag, args.sample))
        if not os.path.isdir(destDir):
            os.makedirs(destDir)
        shutil.move(fileName, os.path.join(destDir, fileNew))
        
    
    
if __name__ == "__main__":
    main()
