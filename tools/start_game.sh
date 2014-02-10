#!/bin/bash

source $(dirname $0)/config

SERVER_BIN=$(dirname $0)/../server/server_main.py

${SERVER_BIN} \
  --proxy_controller=${PROXY_CONTROLLER_HOST}:${PROXY_CONTROLLER_PORT} \
  --proxy=${PROXY_CONTROLLER_HOST}:${PROXY_PORT} \
  --server_port=${SERVER_PORT} \
  --browser=${BROWSER} \
  --chrome_binary=${CHROME_BIN} \
  --chromedriver_binary=${CHROMEDRIVER_BIN}

