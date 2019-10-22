#!/bin/bash

if [ -z "$1" ]; then 
    echo "Flag is not defined, exiting"
    exit 
fi

rm /net/data_cms1b/user/teroerde/Cleaning/data_2018A/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2018B/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2018C/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2018D/* -f

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleMu102X/$1.cuts2018DileptonDoubleMu102X.DoubleMuon_Run2018A.root /net/data_cms1b/user/teroerde/Cleaning/data_2018A/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleMu102X/$1.cuts2018DileptonDoubleMu102X.DoubleMuon_Run2018B.root /net/data_cms1b/user/teroerde/Cleaning/data_2018B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleMu102X/$1.cuts2018DileptonDoubleMu102X.DoubleMuon_Run2018C.root /net/data_cms1b/user/teroerde/Cleaning/data_2018C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleMu102X/$1.cuts2018DileptonDoubleMu102X.DoubleMuon_Run2018D.root /net/data_cms1b/user/teroerde/Cleaning/data_2018D/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleElectron102X/$1.cuts2018DileptonDoubleElectron102X.DoubleElectron_Run2018A.root /net/data_cms1b/user/teroerde/Cleaning/data_2018A/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleElectron102X/$1.cuts2018DileptonDoubleElectron102X.DoubleElectron_Run2018B.root /net/data_cms1b/user/teroerde/Cleaning/data_2018B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleElectron102X/$1.cuts2018DileptonDoubleElectron102X.DoubleElectron_Run2018C.root /net/data_cms1b/user/teroerde/Cleaning/data_2018C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonDoubleElectron102X/$1.cuts2018DileptonDoubleElectron102X.DoubleElectron_Run2018D.root /net/data_cms1b/user/teroerde/Cleaning/data_2018D/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonMuEG102X/$1.cuts2018DileptonMuEG102X.MuEG_Run2018A.root /net/data_cms1b/user/teroerde/Cleaning/data_2018A/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonMuEG102X/$1.cuts2018DileptonMuEG102X.MuEG_Run2018B.root /net/data_cms1b/user/teroerde/Cleaning/data_2018B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonMuEG102X/$1.cuts2018DileptonMuEG102X.MuEG_Run2018C.root /net/data_cms1b/user/teroerde/Cleaning/data_2018C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018DileptonMuEG102X/$1.cuts2018DileptonMuEG102X.MuEG_Run2018D.root /net/data_cms1b/user/teroerde/Cleaning/data_2018D/

python treePostprocessor.py -C CfgMerge/mergeData2018A.ini &
python treePostprocessor.py -C CfgMerge/mergeData2018B.ini &
python treePostprocessor.py -C CfgMerge/mergeData2018C.ini &
python treePostprocessor.py -C CfgMerge/mergeData2018D.ini &

wait

procpath='/net/data_cms1b/user/teroerde/processedTrees/'

hadd ${procpath}$1.processed.MergedData.root ${procpath}data_2018A/$1.processed.MergedData.root ${procpath}data_2018B/$1.processed.MergedData.root ${procpath}data_2018C/$1.processed.MergedData.root ${procpath}data_2018D/$1.processed.MergedData.root


rm /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018Dilepton102X/*.merged
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2018Dilepton102X/ /net/data_cms1b/user/teroerde/trees/$1
rename "cuts2018Dilepton102X" "processed" /net/data_cms1b/user/teroerde/trees/$1/*.root 
mv ${procpath}$1.processed.MergedData.root /net/data_cms1b/user/teroerde/trees/$1/$1.processed.MergedData.root
