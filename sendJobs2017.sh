#!/bin/bash

#python run.py -vf $1 -m Mix/data2017.ini:MET
#python run.py -vf $1 -m Mix/data2017.ini:EE
#python run.py -vf $1 -m Mix/data2017.ini:EMu
#python run.py -vf $1 -m Mix/data2017.ini:MuMu
#python run.py -vf $1 -m Mix/mc2017.ini:full


python run.py -vf $1 -m Mix/signal2017.ini:sbottom
python run.py -vf $1 -m Mix/signal2017.ini:squark

python run.py -vf $1 -m Mix/signal2017.ini:sbottomdenom
python run.py -vf $1 -m Mix/signal2017.ini:squarkdenom
