#!/bin/bash

# Script name is the first parameter on command line
SCRIPT_NAME="$0"

NWAE_UTILS_VERSION=

for keyvalue in "$@"; do
    echo "[$SCRIPT_NAME] Key value pair [$keyvalue]"
    IFS='=' # space is set as delimiter
    read -ra KV <<< "$keyvalue" # str is read into an array as tokens separated by IFS

    if [ "$KV" == "version" ] ; then
        NWAE_UTILS_VERSION=${KV[1]}
        echo "[$SCRIPT_NAME] Set version to $NWAE_UTILS_VERSION."
    fi
done
PYTHON=/usr/local/bin/python3.6
PIP=/usr/local/bin/pip3.6

if [ "$NWAE_UTILS_VERSION" = "" ]; then
  echo "[$SCRIPT_NAME] Must specify version!"
  exit 1
fi

# Clear build folder
rm -rf ./build/*

# Create wheel
$PYTHON src/setup.py bdist_wheel

# Upload to pypi
$PYTHON -m twine upload "dist/nwae.utils-$NWAE_UTILS_VERSION-py3-none-any.whl"

## Uninstall old mozg
#$PIP uninstall nwae.utils
#
## Install back
#$PIP install dist/*.whl
