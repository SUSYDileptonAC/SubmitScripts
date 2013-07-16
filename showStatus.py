#! /usr/bin/env python
'''
Created on 10.08.2009

@author: heron
'''
from optparse import OptionParser
import sys

import src.status
import src.srmTools
from src.mainConfig import MainConfig



def main(argv=None):
    if argv == None:
        argv = sys.argv[1:]

    parser = OptionParser()
    parser.add_option("-C", "--Config", dest="Config", action="append", default=[],
                      help="Main configuration file. Can be given multiple times in case of split configurations. Default is Input/default.ini")
    (opts, args) = parser.parse_args(argv)
    if opts.Config == []:
              opts.Config = [ "Input/default.ini" ]
    settings = MainConfig(opts.Config, opts)

    myStatus = src.status.Status()
    print myStatus.view(src.srmTools.getDir(settings.histogramstoragepath))


if __name__ == '__main__':
    main()
