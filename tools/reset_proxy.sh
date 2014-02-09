#!/bin/bash

source $(dirname $0)/config

CONTROLLER_ADDRESS=http://localhost:${CONTROLLER_PORT}
PROXY_ROOT=${CONTROLLER_ADDRESS}/proxy
PROXY=${PROXY_ROOT}/${PROXY_PORT}

set -e -x

curl -X DELETE ${PROXY}
curl -X POST -d "port=${PROXY_PORT}" ${PROXY_ROOT}
curl -X PUT -d "captureContent=true" ${PROXY}/har

