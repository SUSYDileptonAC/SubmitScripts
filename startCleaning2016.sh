#!/bin/bash

if [ -z "$1" ]; then 
    echo "Flag is not defined, exiting"
    exit 
fi



rm /net/data_cms1b/user/teroerde/Cleaning/data_2016B/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016C/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016D/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016E/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016F/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016G/* -f
rm /net/data_cms1b/user/teroerde/Cleaning/data_2016H/* -f


mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016B.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016C.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016D.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016E.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016F.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016F/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016G.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016G/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleMu102X/$1.cuts2016DileptonDoubleMu102X.DoubleMuon_Run2016H.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016H/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016B.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016C.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016D.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016E.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016F.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016F/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016G.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016G/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonDoubleElectron102X/$1.cuts2016DileptonDoubleElectron102X.DoubleElectron_Run2016H.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016H/

mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016B.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016B/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016C.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016C/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016D.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016D/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016E.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016E/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016F.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016F/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016G.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016G/
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016DileptonMuEG102X/$1.cuts2016DileptonMuEG102X.MuEG_Run2016H.root    /net/data_cms1b/user/teroerde/Cleaning/data_2016H/


python treePostprocessor.py -C CfgMerge/mergeData2016B.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016C.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016D.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016E.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016F.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016G.ini &
python treePostprocessor.py -C CfgMerge/mergeData2016H.ini &
wait


procpath='/net/data_cms1b/user/teroerde/processedTrees/'

hadd ${procpath}$1.processed.MergedData.root  ${procpath}data_2016B/$1.processed.MergedData.root ${procpath}data_2016C/$1.processed.MergedData.root ${procpath}data_2016D/$1.processed.MergedData.root ${procpath}data_2016E/$1.processed.MergedData.root ${procpath}data_2016F/$1.processed.MergedData.root ${procpath}data_2016G/$1.processed.MergedData.root ${procpath}data_2016H/$1.processed.MergedData.root


rm /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016Dilepton102X/*.merged
mv /net/data_cms1b/user/teroerde/AnalysisData/PAT/MergedHistos/$1/cuts2016Dilepton102X/ /net/data_cms1b/user/teroerde/trees/$1
rename "cuts2016Dilepton102X" "processed" /net/data_cms1b/user/teroerde/trees/$1/*.root 
mv ${procpath}$1.processed.MergedData.root /net/data_cms1b/user/teroerde/trees/$1/$1.processed.MergedData.root
