#!/bin/bash

rm /net/data_cms1b/user/teroerde/Cleaning/data_2017B/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2017C/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2017D/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2017E/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2017F/* -f

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleMu102X/$1.cuts2017DileptonDoubleMu102X.DoubleMuon_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_2017B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleMu102X/$1.cuts2017DileptonDoubleMu102X.DoubleMuon_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_2017C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleMu102X/$1.cuts2017DileptonDoubleMu102X.DoubleMuon_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_2017D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleMu102X/$1.cuts2017DileptonDoubleMu102X.DoubleMuon_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_2017E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleMu102X/$1.cuts2017DileptonDoubleMu102X.DoubleMuon_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_2017F/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleElectron102X/$1.cuts2017DileptonDoubleElectron102X.DoubleElectron_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_2017B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleElectron102X/$1.cuts2017DileptonDoubleElectron102X.DoubleElectron_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_2017C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleElectron102X/$1.cuts2017DileptonDoubleElectron102X.DoubleElectron_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_2017D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleElectron102X/$1.cuts2017DileptonDoubleElectron102X.DoubleElectron_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_2017E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonDoubleElectron102X/$1.cuts2017DileptonDoubleElectron102X.DoubleElectron_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_2017F/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonMuEG102X/$1.cuts2017DileptonMuEG102X.MuEG_Run2017B.root /net/data_cms1b/user/teroerde/Cleaning/data_2017B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonMuEG102X/$1.cuts2017DileptonMuEG102X.MuEG_Run2017C.root /net/data_cms1b/user/teroerde/Cleaning/data_2017C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonMuEG102X/$1.cuts2017DileptonMuEG102X.MuEG_Run2017D.root /net/data_cms1b/user/teroerde/Cleaning/data_2017D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonMuEG102X/$1.cuts2017DileptonMuEG102X.MuEG_Run2017E.root /net/data_cms1b/user/teroerde/Cleaning/data_2017E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2017DileptonMuEG102X/$1.cuts2017DileptonMuEG102X.MuEG_Run2017F.root /net/data_cms1b/user/teroerde/Cleaning/data_2017F/

python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunB.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunC.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunD.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunE.ini &
python treePostprocessor.py -C CfgMerge/mergeData2017InclusiveRunF.ini &
wait

procpath='/net/data_cms1b/user/teroerde/processedTrees/'

hadd ${procpath}$1.processed.MergedData.root ${procpath}data_2017B/$1.processed.MergedData.root ${procpath}data_2017C/$1.processed.MergedData.root ${procpath}data_2017D/$1.processed.MergedData.root ${procpath}data_2017E/$1.processed.MergedData.root ${procpath}data_2017F/$1.processed.MergedData.root 
