#!/bin/bash

set -e

TESTDIR="/tmp/testproject"

rm -rf $TESTDIR
mkdir $TESTDIR

# for d in ../forestplots/spss/PMC6112*; do
#  p=`basename ${d}`
#  cp ../forestplots/spss/${p}/fulltext.pdf $TESTDIR/${p}.pdf
# done


for d in ../forestplots/spssSimple/PMC55*; do
 p=`basename ${d}`
 cp ../forestplots/spssSimple/${p}/fulltext.pdf $TESTDIR/${p}.pdf
done

for d in ../forestplots/stataSimple/PMC599*; do
  p=`basename ${d}`
  cp ../forestplots/stataSimple/${p}/fulltext.pdf $TESTDIR/${p}.pdf
done
