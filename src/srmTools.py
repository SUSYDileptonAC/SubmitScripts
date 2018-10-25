'''
Created on 29.07.2009
@author: edelhoff
'''

import os, subprocess, time

def copyFile(source, destination, verbose=False):
    command = 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination
    if (verbose):
        print command

    rc = subprocess.call(command, shell=True)
    time.sleep(0.5)
    return rc


def removeFile(source, verbose=False):
    command = 'srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source
    if (verbose):
        print command

    subprocess.call(command, shell=True)
    return


def getDir(source, verbose=False):
    command = 'srmls -count=2000 -recursion_depth=10 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source
    
    if (verbose): 
        print command
    output = subprocess.check_output(command, shell=True).split() # convert from string to list
    # output is number file number file, so start at second position and skip every second entry from there
    output = output[1::2] # skip numbers in list and only keep files
    output = [o for o in output if (not o.endswith("/"))] # remove folders
    return output


