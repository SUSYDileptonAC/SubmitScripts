#!/usr/bin/env python

def main():
    from ROOT import TFile
    from re import match
    from sys import argv
    from optparse import OptionParser
    from itertools import product

    parser = OptionParser()
    #parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
    #                              help="talk about everything")
    parser.add_option("-i", "--input", dest="inputs", action="append", default=[],
                          help="input files")
    parser.add_option("-e", "--expressions", dest="expressions", action="append", default=[],
                          help="expressions to match")

    (opts, args) = parser.parse_args()

    for path, expression in product(opts.inputs, opts.expressions):
        print "=== %s: %s ===" % (path, expression)
        theFile = TFile(path)
        hltHisto = theFile.FindObjectAny("Trigger paths")
        print hltHisto
        axis = hltHisto.GetXaxis()
        for i in range(1, hltHisto.GetNbinsX() + 1):
            if not match(expression, axis.GetBinLabel(i)) == None:
                print i, axis.GetBinLabel(i), hltHisto.GetBinContent(i)

if __name__ == "__main__":
    main()
