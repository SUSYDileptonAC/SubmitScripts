'''
Created on 29.07.2009

@author: edelhoff
'''

import os, subprocess

def copyFile(source, destination, verbose=False):
    if (verbose):
        print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination
    #print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination
#lcg-cp -v -b -D srmv2 SURL  file://local_file

    #~ print 'srmcp srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv1?SFN=' + source + ' file:///' + destination
    subprocess.call(['lcg-cp  -b -D srmv2  srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source + ' file:///' + destination], shell=True)
    #time.sleep(1)
    return


def removeFile(source, verbose=False):
    if (verbose):
        print 'srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source

    #~ subprocess.call(['srmrm srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source], shell=True)
    #~ print source
    subprocess.call(['lcg-del  -b -l -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source], shell=True)
    #time.sleep(1)
    return


def getDir(source, verbose=False):
    command = 'srmls -count=950 -recursion_depth=10 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source
    command2 = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + source
    #~ print source

    if (verbose): print command
    #~ output = __getCommandOutput2(command)
    output = __getCommandOutput2(command2)
    #~ print output
    if (verbose):
        print "Output:\n" + output
    if (len(output.splitlines()) >= 950):
        print "Warning: list probably not complete!"
        #raise StandardError, "More than 999 entries found in directory. Aborting!"

    returnValue = []

    # find all occurrences of source - all directory entries
    i = 0
    while (output.find(source, i, len(output)) != -1):
        nextOccurrence = output.find(source, i, len(output))
        entry = output[nextOccurrence:output.find('\n', nextOccurrence, len(output))]
        command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry
        output_2 = __getCommandOutput2(command)
        j = 0
        while (output_2.find(entry, j, len(output_2)) != -1):
            nextOccurrence_2 = output_2.find(entry, j, len(output_2))
            entry_2 = output_2[nextOccurrence_2:output_2.find('\n', nextOccurrence_2, len(output_2))]
            command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry_2
            output_3 = __getCommandOutput2(command)
            k = 0
            while (output_3.find(entry, k, len(output_3)) != -1):
                nextOccurrence_3 = output_3.find(entry, k, len(output_3))
                entry_3 = output_3[nextOccurrence_3:output_3.find('\n', nextOccurrence_3, len(output_3))]
                command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry_3
                output_4 = __getCommandOutput2(command)
                l = 0
                while (output_4.find(entry, l, len(output_4)) != -1):
                    nextOccurrence_4 = output_4.find(entry, l, len(output_4))
                    entry_4 = output_4[nextOccurrence_4:output_4.find('\n', nextOccurrence_4, len(output_4))]
                    command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry_4
                    output_5 = __getCommandOutput2(command)
                    m = 0
                    while (output_5.find(entry, m, len(output_5)) != -1):
                        nextOccurrence_5 = output_5.find(entry, m, len(output_5))
                        entry_5 = output_5[nextOccurrence_5:output_5.find('\n', nextOccurrence_5, len(output_5))]
                        command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry_5
                        output_6 = __getCommandOutput2(command)
                        n = 0
                        while (output_6.find(entry, n, len(output_6)) != -1):
                            nextOccurrence_6 = output_6.find(entry, n, len(output_6))
                            entry_6 = output_6[nextOccurrence_6:output_6.find('\n', nextOccurrence_6, len(output_6))]
                            if not "failed" in entry_6 and (entry_6 != entry_5):
                                if "log" in entry_6:
                                    command = 'lcg-ls  -b -D srmv2 srm://grid-srm.physik.rwth-aachen.de:8443/srm/managerv2?SFN=' + entry_6
                                    output_7 = __getCommandOutput2(command)
                                    o = 0
                                    while (output_7.find(entry, o, len(output_7)) != -1):
                                        nextOccurrence_7 = output_7.find(entry, o, len(output_7))
                                        entry_7 = output_7[nextOccurrence_7:output_7.find('\n', nextOccurrence_7, len(output_7))]
                                        o = output_7.find(entry, o, len(output_7)) + 1
                                        #print entry_7
                                        if (entry_7 != entry_6):
                                            returnValue.append(entry_7)
                                else:
                                    returnValue.append(entry_6)
                            n = output_6.find(entry, n, len(output_6)) + 1
                            
                        m = output_5.find(entry, m, len(output_5)) + 1
                    
                    l = output_4.find(entry, l, len(output_4)) + 1
                
                k = output_3.find(entry, k, len(output_3)) + 1

            j = output_2.find(entry, j, len(output_2)) + 1
            
                 

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
