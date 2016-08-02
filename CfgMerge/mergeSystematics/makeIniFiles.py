#!/usr/bin/env python



def saveIni(ini, name):
	iniFile = open("mergeSimulationMiniAOD_%s.ini"%name, "w")
	iniFile.write(ini)
	iniFile.close()

				  


def main():
	from sys import argv
	

	iniTemplate =r"""
[general]
tasks = cutsV33DileptonMiniAODSystematics
basePath = /disk1/user/schomakers/trees/Cleaning/SystematicTrees/%s
MCDatasets = .*
counterSum = True
outPath = /disk1/user/schomakers/trees/processedTrees/SystematicTrees/m_sbottom_%s_m_neutralino_%s

[dileptonTree:cutsV33Dilepton]
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
EEExpression = ((pt1 > 20 && pt2 > 10) || (pt1 > 10 && pt2 > 20)) && mSbottom == %d && mNeutralino2 < %d && mNeutralino2 > %d
EMuExpression = ((pt1 > 20 && pt2 > 10) || (pt1 > 10 && pt2 > 20)) && mSbottom == %d && mNeutralino2 < %d && mNeutralino2 > %d
MuMuExpression = ((pt1 > 20 && pt2 > 10) || (pt1 > 10 && pt2 > 20))  && mSbottom == %d && mNeutralino2 < %d && mNeutralino2 > %d



[treeProcessor:overlapHighPt]
type = OverlapRemover
listPath = events.highPt
EEProcessors = highPtSelector
EMuProcessors = highPtSelector
MuMuProcessors = highPtSelector
"""


	sbottom_masses = [400,425,450,475,500,525,550,575,600,625,650,675,700,725,750,775,800,850,900,950]
	
	for m_sbottom in sbottom_masses:
		if m_sbottom < 600:
			neutralino_masses = [150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,525,550]
			mass_range = "lowMass"
		elif m_sbottom < 800:
			neutralino_masses = [150,175,200,225,250,275,300,325,350,375,400,425,450,475,500,525,550,575,600,625,650,675,700,725]
			mass_range = "mediumMass"
		else:
			neutralino_masses = [150,200,250,300,350,400,450,500,550,600,650,700,750,800,850,900]
			mass_range = "highMass"
			
		for m_neutralino in neutralino_masses:
			if m_neutralino < m_sbottom:
				m_neutr_min = m_neutralino - 5
				m_neutr_max = m_neutralino + 5
				
				masses = "%s_%s"%(str(m_sbottom),str(m_neutralino))
		
	
	
		
				saveIni(iniTemplate%(mass_range,str(m_sbottom),str(m_neutralino),m_sbottom,m_neutr_max,m_neutr_min,m_sbottom,m_neutr_max,m_neutr_min,m_sbottom,m_neutr_max,m_neutr_min), masses)
				
	sbottom_masses = [400,425,450,475,500,525,550,575,600,625,650,675,700,725,750,775,800,850,900,950]
	
	#~ for m_sbottom in sbottom_masses:
		#~ neutralino_masses = [120,130,140]
		#~ mass_range = "lowChi2"
		#~ 
			#~ 
		#~ for m_neutralino in neutralino_masses:
			#~ if m_neutralino < m_sbottom:
				#~ m_neutr_min = m_neutralino - 5
				#~ m_neutr_max = m_neutralino + 5
				#~ 
				#~ masses = "%s_%s"%(str(m_sbottom),str(m_neutralino))
		#~ 
	#~ 
	#~ 
		#~ 
				#~ saveIni(iniTemplate%(mass_range,str(m_sbottom),str(m_neutralino),m_sbottom,m_neutr_max,m_neutr_min,m_sbottom,m_neutr_max,m_neutr_min,m_sbottom,m_neutr_max,m_neutr_min), masses)


main()
