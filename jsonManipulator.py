#! /usr/bin/env python

import sys
from optparse import OptionParser
from pprint import pformat

def main():
    # create option parser
    parser = OptionParser()
    parser.add_option("-v", "--verbose", action="store_true", dest="verbose", default=False,
                      help="Verbose mode.")
    parser.add_option("-i", "--imput", dest="inputFile", nargs=1, default="jsonls.txt",
                      help="json file to be read in")
    parser.add_option("-m", "--min", dest="min", nargs=1, default=0,
                      help="Minimal run number")
    parser.add_option("-M", "--max", dest="max", nargs=1, default=999999999,
                      help="Maximal run number")

    argv = sys.argv[1:]
    (opts, args) = parser.parse_args(argv)

    # read in
    print "reading in %s" % opts.inputFile
    json = None
    with open(opts.inputFile, "r") as file:
        json = eval(file.read())
        print json

    # filter json file
    json = filter(json, int(opts.min), int(opts.max))
    print "\n======== filtered to ========"

    # write out
    print json
    with open(opts.inputFile + ".new", "w") as file:
        outString = pformat(json)
        outString = outString.replace("'", '"')
        file.write(outString)

    return


def filter(json, minNr, maxNr):
    jsonNew = {}
    for key in json.keys():
        runNr = int(key)
        if (minNr <= runNr and runNr <= maxNr):
            jsonNew.update({key: json[key]})
        #print "%d, %d, %d" % (runNr, minNr, maxNr)
    return jsonNew


# entrypoint
if (__name__ == "__main__"):
    main()

