#!/bin/bash

# Use this script as the git pre-commit.
#   ln -s ../../pre-commit.sh .git/hooks/pre-commit

# Run KCAA server tests.
KCAA_SERVER_ROOT=${PWD}/server
export PYTHONPATH=${KCAA_SERVER_ROOT}
python ${KCAA_SERVER_ROOT}/__init__.py
