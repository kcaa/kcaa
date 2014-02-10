#!/bin/bash

source $(dirname $0)/config

PROXY_CONTROLLER_ADDRESS=http://${PROXY_CONTROLLER_HOST}:${PROXY_CONTROLLER_PORT}
PROXY_ROOT=${PROXY_CONTROLLER_ADDRESS}/proxy

curl -s -X DELETE ${PROXY_ROOT}/${PROXY_PORT}
curl -s -X POST -d "port=${PROXY_PORT}" ${PROXY_ROOT} > /dev/null
curl -s -X PUT -d "captureContent=true"'&'"initialPageRef=1" \
  ${PROXY_ROOT}/${PROXY_PORT}/har

