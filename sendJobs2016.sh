#!/bin/bash

./run.py -vf $1 -C Input/default80X.ini -C Input/25nsData_80X.ini -C Analyzers/finalTreesNoTausMiniAOD.ini -t cutsV34DileptonDoubleMu -gG "DoubleMu" 

./run.py -vf $1 -C Input/default80X.ini -C Input/25nsData_80X.ini -C Analyzers/finalTreesNoTausMiniAOD.ini -t cutsV34DileptonDoubleElectron -gG "DoubleElectron" 

./run.py -vf $1 -C Input/default80X.ini -C Input/25nsData_80X.ini -C Analyzers/finalTreesNoTausMiniAOD.ini -t cutsV34DileptonMuEG -gG "MuEG" 

./run.py -vf $1 -C Input/default80X.ini -C Input/25nsMC_80X.ini -C Analyzers/finalTreesNoTausMiniAODMC.ini -t cutsV34Dilepton -gG "MC" 
