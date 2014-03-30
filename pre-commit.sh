#!/bin/bash

# Use this script as the git pre-commit.
#   ln -s ../../pre-commit.sh .git/hooks/pre-commit

# Run KCAA server tests.
# TODO: Run all doctests as well.
KCAA_SERVER_ROOT=${PWD}/server
export PYTHONPATH=${KCAA_SERVER_ROOT}
py.test ${KCAA_SERVER_ROOT}
