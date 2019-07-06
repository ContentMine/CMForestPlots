#!/bin/bash

set -e

TESTDIR="/tmp/testproject"

rm -rf $TESTDIR
mkdir $TESTDIR


for d in ../forestplots/spssSimple/PMC*; do
  p=`basename ${d}`
  cp ../forestplots/spssSimple/${p}/fulltext.pdf $TESTDIR/${p}.pdf
done

