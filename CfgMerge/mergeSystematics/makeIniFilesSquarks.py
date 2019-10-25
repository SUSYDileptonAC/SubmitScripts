#!/usr/bin/env python



def saveIni(ini, year, name):
        import os
        folder = "%s/T6qqllslepton"%year
        if not os.path.isdir(folder):
                os.makedirs(folder)
        iniFile = open("%s/splitSquarkSignal_%s.ini"%(folder,name), "w")
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
basePath = /net/data_cms1b/user/teroerde/Cleaning/Signals/T6qqllslepton/{baseName}
MCDatasets = .*
counterSum = True
outPath = /net/data_cms1b/user/teroerde/processedTrees/Signals/T6qqllslepton/m_squark_{msquark}_m_neutralino_{mneutralino2}

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
EEExpression =   mLightSquarks == {msquark} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}
EMuExpression =  mLightSquarks == {msquark} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}
MuMuExpression = mLightSquarks == {msquark} && mNeutralino2 > {mneutralino2_min} && mNeutralino2 < {mneutralino2_max}



[treeProcessor:overlapHighPt]
type = OverlapRemover
listPath = events.highPt
EEProcessors = highPtSelector
EMuProcessors = highPtSelector
MuMuProcessors = highPtSelector
"""


        squark_masses = range(1000, 2150, 50)

        
        
        for m_squark in squark_masses:
                neutralino_masses = range(150, 2100, 50)
                baseName = "msquark_1000To2100_GeV"
  
                
     
                        
                for m_neutralino in neutralino_masses:
                        if m_neutralino < m_squark:
                                m_neutr_min = m_neutralino - 5
                                m_neutr_max = m_neutralino + 5
                                
                                masses = "%s_%s"%(str(m_squark),str(m_neutralino))
                                
                                tmp = iniTemplate.format(year = args.year,msquark=m_squark, mneutralino2=m_neutralino, mneutralino2_min=m_neutr_min, mneutralino2_max=m_neutr_max, baseName=baseName)
                                
                                saveIni(tmp, args.year, masses)
                        else:
                                break
                                


main()
