#!/bin/bash

while :
do
    python getOutputFromStorage2.py -C Input/default80X.ini
	echo "Press [CTRL+C] to stop.."
	sleep 60
done
