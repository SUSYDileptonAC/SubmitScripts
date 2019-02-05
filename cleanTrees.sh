#!/bin/bash

NUMBER=0
FILES="$(< iniFiles.txt)" #names from names.txt file
for FILE in $FILES; do
        echo $FILE
        python treePostprocessorSignal.py -C CfgMerge/mergeSystematics/$FILE &
        NUMBER=$((NUMBER + 1))
        if (( $NUMBER % 15 == 0 )); then wait; fi
done
wait
