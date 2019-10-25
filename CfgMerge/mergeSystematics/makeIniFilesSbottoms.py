#!/usr/bin/env python



def saveIni(ini, year, name):
        import os
        folder = "%s/T6bbllslepton"%year
        if not os.path.isdir(folder):
                os.makedirs(folder)
        iniFile = open("%s/splitSbottomSignal_%s.ini"%(folder,name), "w")
        iniFile.write(ini)
        iniFile.close()

                                  


def main():
        from sys import argv
        import argparse
        parser = argparse.ArgumentParser(description='Ini file generator')
        parser.add_argument("-y", "--year",action="store", dest="year", default="2017",
                                                  help="For which year?")
        args = parser.parse_args()
        
        iniTemplate =r"""
[general]
tasks = cuts{year}DileptonSignal
basePath = /net/data_cms1b/user/teroerde/Cleaning/Signals/T6bbllslepton/{baseName}
MCDatasets = .*
counterSum = True
outPath = /net/data_cms1b/user/teroerde/processedTrees/Signals/T6bbllslepton/m_sbottom_{msbottom}_m_neutralino_{mneutralino2}

[dileptonTree:cuts{year}DileptonSignal]
treeProducerName = FinalTrees
objects = EE EMu MuMu

EEDataset = .*
EESelection = 
EEProcessors = overlapHighPt
EEFilter = highPtSelector

EMuDataset = .*
EMuSelection = 
EMuProcessors = overlapHighPt
EMuFilter = highPtSelector

MuMuDataset = .*
MuMuSelection = 
MuMuProcessors = overlapHighPt
MuMuFilter = highPtSelector

OtherSelection = 

# remove ID selection for overlap checking
#  -> possible only if running over trees with only tight leptons
[treeProcessor:highPtSelector]
type = SimpleSelector
EEExpression =   mSbottom == {msbottom} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}
EMuExpression =  mSbottom == {msbottom} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}
MuMuExpression = mSbottom == {msbottom} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}



[treeProcessor:overlapHighPt]
type = OverlapRemover
listPath = events.highPt
EEProcessors = highPtSelector
EMuProcessors = highPtSelector
MuMuProcessors = highPtSelector
"""


        #sbottom_masses = [400,425,450,475,500,525,550,575,600,625,650,675,700,725,750,775,800,850,900,950,1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600]
        #sbottom_masses = [1000,1050,1100,1150,1200,1250,1300,1350,1400,1450,1500,1550,1600]
        #sbottom_masses = range(400, 1825, 25)
        #sbottom_masses = range(800, 1825, 25)
        sbottom_masses = range(800, 1850, 50)
        #sbottom_masses = range(400, 1400, 25)+ range(1400, 1850, 50)
        
        
        for m_sbottom in sbottom_masses:
                if m_sbottom < 800:
                        neutralino_masses = range(150, 800, 50)
                        #neutralino_masses = range(150, 800, 25)
                        baseName = "msbottom_400To775_GeV"
                elif m_sbottom < 1400:
                        #neutralino_masses = range(150, 1400, 25)
                        neutralino_masses = range(150, 1400, 50)
                        baseName = "msbottom_800To1375_GeV"
                else:
                        #neutralino_masses = range(150, 1150, 50)+range(1125, 1800, 25)
                        neutralino_masses = range(150, 1800, 50)
                        #neutralino_masses = range(150, 1150, 50)+range(1125, 1800, 50)
                        baseName = "msbottom_1400To1800_GeV"
                
     
                        
                for m_neutralino in neutralino_masses:
                        if m_neutralino < m_sbottom:
                                m_neutr_min = m_neutralino - 5
                                m_neutr_max = m_neutralino + 5
                                
                                masses = "%s_%s"%(str(m_sbottom),str(m_neutralino))
                                
                                tmp = iniTemplate.format(year = args.year,msbottom=m_sbottom, mneutralino2=m_neutralino, mneutralino2_min=m_neutr_min, mneutralino2_max=m_neutr_max, baseName=baseName)
                                
                                saveIni(tmp, args.year, masses)
                        else:
                                break

main()
