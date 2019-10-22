#!/bin/bash

python run.py -vf $1 -m Mix/mc2016.ini:full
#python run.py -vf $1 -m Mix/data2016.ini:HT
python run.py -vf $1 -m Mix/data2016.ini:EE
python run.py -vf $1 -m Mix/data2016.ini:EMu
python run.py -vf $1 -m Mix/data2016.ini:MuMu
