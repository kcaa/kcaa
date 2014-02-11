#!/bin/bash

source $(dirname $0)/config

exec ${PROXY_CONTROLLER_BIN} --port=${PROXY_CONTROLLER_PORT}
