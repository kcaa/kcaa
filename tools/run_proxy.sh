#!/bin/bash

source $(dirname $0)/config

${CONTROLLER_BIN} --port=${CONTROLLER_PORT}
