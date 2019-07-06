#!/bin/bash

set -e

function usage() {
    echo "test.sh PROJECT_DIRECTORY"
}

function die() {
    echo >&2 "Error: $@"
    exit 1
}

if [ $# -ne 1 ]; then
    usage
    exit 1
fi

PROJECT_FOLDER=$1
[ -d "$PROJECT_FOLDER" ] || die "${PROJECT_FOLDER}: not a directory."

IMAGE_NAME="forestplot"

function docker_wrapper() {
    COMMAND=$1
    shift

    echo "Running ${COMMAND}..."
    docker run -it --rm -v $PROJECT_FOLDER:/tmp/project $IMAGE_NAME $COMMAND -p /tmp/project $@ >> /tmp/forestplot.log
    echo "Done"
}

docker_wrapper ami-makeproject --rawfiletypes html,pdf,xml --omit template.xml log.txt

docker_wrapper ami-pdf

# Now analyse the image to check for partitions
for t in 150; do

    echo "Testing with boundaries at ${t} threshold..."

    docker_wrapper ami-image --sharpen sharpen4 --threshold ${t} --despeckle true
    docker_wrapper ami-pixel --projections --yprojection 0.4 --xprojection 0.7 --lines --minheight -1 \
        --rings -1 --islands 0 --inputname raw_s4_thr_${t}_ds


#
#     docker_wrapper ami-pixel --projections --yprojection 0.4 --xprojection 0.7 --lines --minheight -1 \
#         --rings -1 --islands 0 --inputname raw_s4_thr_${t}_ds --subimage statascale y 2 delta 10 projection x \
#         --templateinput raw_s4_thr_${t}_ds/projections.xml --templateoutput template.xml \
#         --templatexsl /org/contentmine/ami/tools/spssTemplate.xsl
done





#     docker_wrapper ami-forestplot --segment --template raw_s4_thr_${t}_ds/template.xml
#
#     invalid=0
#     for d in raw.header.tableheads raw.header.graphheads raw.body.table raw.body.graph raw.footer.summary raw.footer.scale; do
#         width=`identify -format "%w" ${d}.png`
#         height=`identify -format "%h" ${d}.png`
#         if [ $width -lt 20 -o $height -lt 20 ]; then
#             invalid=1
#             break
#         fi
#     done
#     if [ $invalid -eq 1 ]; then
#         echo "Skipping "
#         continue
#     fi
# done

#     for d in raw.header.tableheads raw.header.graphheads raw.body.table raw.body.graph raw.footer.summary raw.footer.scale; do
#         docker_wrapper ami-image --inputname $d --sharpen sharpen4 --threshold ${t} --despeckle true
#     done
#
#     for d in raw.header.tableheads raw.header.graphheads raw.body.table raw.footer.summary raw.footer.scale; do
#         docker_wrapper ami-ocr --inputname ${d}_s4_thr_${t}_ds --tesseract /usr/bin/tesseract --extractlines hocr #--forcemake
#         #docker_wrapper ami-ocr --inputname ${d}_s4_thr_${t}_ds --gocr /usr/bin/gocr --extractlines gocr #--forcemake
#     done
#
#     for d in gocr hocr; do
#         docker_wrapper ami-forestplot --inputname raw.body.table_s4_thr_${t}_ds --table ${d}/${d}.svg --tableType ${d}
#     done
# done
