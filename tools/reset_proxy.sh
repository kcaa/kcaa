#!/bin/bash

source $(dirname $0)/config

PROXY_CONTROLLER_ADDRESS=http://${PROXY_CONTROLLER_HOST}:${PROXY_CONTROLLER_PORT}
PROXY_ROOT=${PROXY_CONTROLLER_ADDRESS}/proxy

curl -X DELETE ${PROXY_ROOT}/${PROXY_PORT}
curl -X POST -d "port=${PROXY_PORT}" ${PROXY_ROOT}
curl -X PUT -d "captureContent=true" ${PROXY_ROOT}/${PROXY_PORT}/har

