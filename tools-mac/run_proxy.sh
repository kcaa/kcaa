#!/bin/bash

source $(dirname $0)/config

export JAVA_OPTS="-Xmx${PROXY_CONTROLLER_HEAPSIZE}"
exec ${PROXY_CONTROLLER_BIN} --port=${PROXY_CONTROLLER_PORT}
