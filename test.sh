#!/bin/bash

set -e

function die() {
    echo >&2 "Error: $@"
    exit 1
}

PROJECT_FOLDER="$1"
[ -d "$PROJECT_FOLDER" ] || die "${PROJECT_FOLDER}: not a directory."

