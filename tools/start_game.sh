#!/bin/bash

source $(dirname $0)/config

SERVER_BIN=$(dirname $0)/../server/server_main.py
RUN_PROXY_BIN=$(dirname $0)/run_proxy.sh

function on_exit() {
  if [ -n "${PROXY_CONTROLLER_PID}" ]; then
    echo "Killing the controller of pid ${PROXY_CONTROLLER_PID}"
    kill ${PROXY_CONTROLLER_PID}
  fi
}
trap on_exit EXIT

if ((!PROXY_CONTROLLER_DAEMON)); then
  ${RUN_PROXY_BIN} &
  PROXY_CONTROLLER_PID=$!
  echo "Proxy controller running at pid ${PROXY_CONTROLLER_PID}"
fi

${SERVER_BIN} \
  --proxy_controller=${PROXY_CONTROLLER_HOST}:${PROXY_CONTROLLER_PORT} \
  --proxy=${PROXY_CONTROLLER_HOST}:${PROXY_PORT} \
  --server_port=${SERVER_PORT} \
  --browser=${BROWSER} \
  --chrome_binary=${CHROME_BIN} \
  --chromedriver_binary=${CHROMEDRIVER_BIN} \
  --credentials=${CREDENTIALS}
