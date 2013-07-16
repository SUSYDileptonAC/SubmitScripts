import pickle


def getWeight(nVertices= -1):
    pickleFile = "weights.pkl"
    pFile = open(pickleFile, 'rb')
    weightDict = pickle.load(pFile)
    pFile.close()

    value = None
    key = "%d" % nVertices
    if (nVertices == -1):
        value = weightDict
    else:
        if (weightDict.has_key(key)):
            value = weightDict[key]

    return value


def getWeightString():
    string = None

    pickleFile = "weights.pkl"
    pFile = open(pickleFile, 'rb')
    weightDict = pickle.load(pFile)
    pFile.close()

    for i in range(1, 30):
        key = "%d" % i
        if (string == None):
            string = "%f * (nVertices == %d)" % (weightDict[key], i)
        else:
            string = "%s + %f * (nVertices == %d)" % (string, weightDict[key], i)

    string = "(%s)" % string
    return string
