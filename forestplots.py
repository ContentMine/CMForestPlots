#!/usr/bin/env python3

import os
import sys

import forestplots

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("USAGE: {0} PROJECT_DIRECTORY".format(sys.argv[0]))
        sys.exit(-1)

    if not os.path.isdir(sys.argv[1]):
        print("USAGE: {0} PROJECT_DIRECTORY".format(sys.argv[0]))
        sys.exit(-1)

    c = forestplots.Controller(sys.argv[1])
    c.main()
