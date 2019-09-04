#!/bin/bash

set -e

function usage {
    echo "Usage: $0 [PATH TO PDF FOLDER]"
    exit 1
}

if [ "$#" -ne 1 ]; then
    usage
fi

if ! [ -d $1 ]; then
    usage
fi

docker run -it --rm -v $1:/tmp/project forestplot python3.7 forestplots.py /tmp/project
