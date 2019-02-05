#!/bin/bash

./run.py -vf $1 -C Input/default94X.ini -C Input/25nsData_94X.ini -C Analyzers/finalTreesNoTausMiniAOD94X.ini -t cutsV34DileptonDoubleMu94X -gG "DoubleMu" 

./run.py -vf $1 -C Input/default94X.ini -C Input/25nsData_94X.ini -C Analyzers/finalTreesNoTausMiniAOD94X.ini -t cutsV34DileptonDoubleElectron94X -gG "DoubleElectron" 

./run.py -vf $1 -C Input/default94X.ini -C Input/25nsData_94X.ini -C Analyzers/finalTreesNoTausMiniAOD94X.ini -t cutsV34DileptonMuEG94X -gG "MuEG"
 
#./run.py -vf $1 -C Input/default94X.ini -C Input/25nsData_94X.ini -C Analyzers/finalTreesNoTausMiniAOD94X.ini -t cutsV34DileptonTriggerPFMET94X -gG "MET" 

./run.py -vf $1 -C Input/default94X.ini -C Input/25nsMC_94X.ini -C Analyzers/finalTreesNoTausMiniAODMC94X.ini -t cutsV34Dilepton94X -gG "MC" 
