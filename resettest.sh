#!/bin/bash

set -e

TESTDIR="/tmp/testproject"

rm -rf $TESTDIR
mkdir $TESTDIR

for d in ../forestplots/spssSimple/PMC550*; do
 p=`basename ${d}`
 cp ../forestplots/spssSimple/${p}/fulltext.pdf $TESTDIR/${p}.pdf
done

# for d in ../forestplots/stataSimple/PMC*; do
#   p=`basename ${d}`
#   cp ../forestplots/stataSimple/${p}/fulltext.pdf $TESTDIR/${p}.pdf
# done
#
# for d in ../forestplots/spssSubplot/PMC611*; do
#   p=`basename ${d}`
#   cp ../forestplots/spssSubplot/${p}/fulltext.pdf $TESTDIR/${p}.pdf
# done
