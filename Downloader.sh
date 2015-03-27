#!/bin/bash

while :
do
    python getOutputFromStorage2.py -C Input/default70X.ini
	echo "Press [CTRL+C] to stop.."
	sleep 60
done
