#!/bin/bash

PYTHON=/usr/local/bin/python3.6
PIP=/usr/local/bin/pip3.6

# Clear build folder
rm -rf ./build/*

# Create wheel
$PYTHON src/setup.py bdist_wheel

# Uninstall old mozg
$PIP uninstall mozg.utils

# Install back
$PIP install dist/*.whl

# Copy over to another project
cp dist/*.whl ../mozg.nlp/wheels