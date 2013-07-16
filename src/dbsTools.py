import os, subprocess

def getNumEvents(datasetpath):
    return int(parseDBSQL('find sum(file.numevents) where dataset = '+datasetpath)[0])

def getParent(datasetpath):
    return (parseDBSQL('find dataset.parent where dataset = '+datasetpath)[0])

def parseDBSQL(searchstring):
    command = 'dbsql "%s"' %(searchstring)
    raw_List = __getCommandOutput2(command).split('\n')[4:-1]
    list = []
    for item in raw_List:
        list.append(item.strip())
    return list

def __getCommandOutput2(command):
    child = os.popen(command)
    data = child.read()
    err = child.close()
    if err:
        raise RuntimeError, '%s failed w/ exit code %d' % (command, err)
    return data
