#!/bin/bash

FILES="$(< iniFiles.txt)" #names from names.txt file
for FILE in $FILES; do
	echo $FILE
	python treePostprocessorSignal.py -C CfgMerge/mergeSystematics/$FILE
done
