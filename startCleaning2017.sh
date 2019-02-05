#!/bin/bash

#rm /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunB/* -f
#rm /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunC/* -f
#rm /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunD/* -f
#rm /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunE/* -f
#rm /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunF/* -f

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleMu94X/$1.cutsV34DileptonDoubleMu94X.DoubleMuon_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunB/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleMu94X/$1.cutsV34DileptonDoubleMu94X.DoubleMuon_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunC/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleMu94X/$1.cutsV34DileptonDoubleMu94X.DoubleMuon_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunD/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleMu94X/$1.cutsV34DileptonDoubleMu94X.DoubleMuon_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunE/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleMu94X/$1.cutsV34DileptonDoubleMu94X.DoubleMuon_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunF/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleElectron94X/$1.cutsV34DileptonDoubleElectron94X.DoubleElectron_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunB/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleElectron94X/$1.cutsV34DileptonDoubleElectron94X.DoubleElectron_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunC/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleElectron94X/$1.cutsV34DileptonDoubleElectron94X.DoubleElectron_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunD/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleElectron94X/$1.cutsV34DileptonDoubleElectron94X.DoubleElectron_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunE/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonDoubleElectron94X/$1.cutsV34DileptonDoubleElectron94X.DoubleElectron_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunF/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonMuEG94X/$1.cutsV34DileptonMuEG94X.MuEG_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunB/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonMuEG94X/$1.cutsV34DileptonMuEG94X.MuEG_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunC/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonMuEG94X/$1.cutsV34DileptonMuEG94X.MuEG_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunD/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonMuEG94X/$1.cutsV34DileptonMuEG94X.MuEG_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunE/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cutsV34DileptonMuEG94X/$1.cutsV34DileptonMuEG94X.MuEG_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_94X_RunF/

python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunB.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunC.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunD.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunE.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunF.ini &
wait
