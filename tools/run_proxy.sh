#!/bin/bash

source $(dirname $0)/proxy_config

${CONTROLLER_BIN} --port=${CONTROLLER_PORT}
