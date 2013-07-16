#!/bin/bash

echo "Setting up another screen"

screen -S $1 -X split
screen -S $1 -X focus down
screen -S $1 -X screen bash
sleep 2

screen -S $1 -X stuff $'cd\r'
screen -S $1 -X stuff $'source .bash_profile\r'
screen -S $1 -X stuff $'cd SUSY/SubmitScripts/JobDB\r'
screen -S $1 -X stuff $'while [ -e runSwitch ]; do ./claimJob.py -fC cmssmScans.ini; sleep 1; done\r'

