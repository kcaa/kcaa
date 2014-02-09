#!/bin/bash

source $(dirname $0)/config

${PROXY_CONTROLLER_BIN} --port=${PROXY_CONTROLLER_PORT}
