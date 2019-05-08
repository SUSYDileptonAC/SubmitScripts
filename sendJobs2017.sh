#!/bin/bash

python run.py -vf $1 -m Mix/mc2017.ini:full
python run.py -vf $1 -m Mix/data2017.ini:MET
python run.py -vf $1 -m Mix/data2017.ini:EE
python run.py -vf $1 -m Mix/data2017.ini:EMu
python run.py -vf $1 -m Mix/data2017.ini:MuMu

