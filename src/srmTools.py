'''
Created on 29.07.2009

@author: edelhoff
'''

import os, subprocess

def copyFile(source, destination, verbose=False):
    if (verbose):
        print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination

    subprocess.call(['srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination], shell=True)
    #time.sleep(1)
    return


def removeFile(source, verbose=False):
    if (verbose):
        print 'srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source

    subprocess.call(['srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source], shell=True)
    #time.sleep(1)
    return


def getDir(source, verbose=False):
    command = 'srmls -count=800 -recursion_depth=1000 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source

    if (verbose): print command
    output = __getCommandOutput2(command)
    if (verbose):
        print "Output:\n" + output
    if (len(output.splitlines()) >= 800):
        print "Warning: list probably not complete!"
        #raise StandardError, "More than 999 entries found in directory. Aborting!"

    returnValue = []

    # find all occurrences of source - all directory entries
    i = 0
    while (output.find(source, i, len(output)) != -1):
        nextOccurrence = output.find(source, i, len(output))
        #print nextOccurrence
        # ignore first occurrence - is directory itself
        if (nextOccurrence != output.find(source)):
            entry = output[nextOccurrence:output.find('\n', nextOccurrence, len(output))]
            #print entry
            returnValue.append(entry)

        i = output.find(source, i, len(output)) + 1

    return returnValue


def __getCommandOutput2(command):
    child = os.popen(command)
    data = child.read()
    err = child.close()
    if err:
        if int(err) == 256:
            print 'Path in %s does not exist!' % (command)
            return ' '
        else:
            raise RuntimeError, '%s failed w/ exit code %d' % (command, err)
    return data
