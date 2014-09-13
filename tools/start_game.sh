#!/bin/bash
#
# You need to run './run_proxy.sh' as a separate job if you set
# PROXY_CONTROLLER_DAEMON=1.
#
# You need to run 'sudo xinit' in a separate job, and 'export DISPLAY=:0.0'
# before running './start_game.sh' in the same session if you running this
# script from non-GUI environment.

SCRIPT_DIR=$(dirname $0)
CONFIG_FILE=${1-${SCRIPT_DIR}/config}

source ${CONFIG_FILE}

SERVER_BIN=${SCRIPT_DIR}/../server/server_main.py
RUN_PROXY_BIN=${SCRIPT_DIR}/run_proxy.sh

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
  --backend_update_interval=${BACKEND_UPDATE_INTERVAL} \
  --kancolle_browser=${KANCOLLE_BROWSER} \
  --kcaa_browser=${KCAA_BROWSER} \
  --show_kancolle_screen=${SHOW_KANCOLLE_SCREEN} \
  --frontend_update_interval=${FRONTEND_UPDATE_INTERVAL} \
  --chrome_binary=${CHROME_BIN} \
  --chromium_binary=${CHROMIUM_BIN} \
  --chrome_user_data_basedir=${CHROME_USER_DATA_BASEDIR} \
  --chromedriver_binary=${CHROMEDRIVER_BIN} \
  --phantomjs_binary=${PHANTOMJS_BIN} \
  --preferences=${PREFERENCES} \
  --credentials=${CREDENTIALS} \
  --debug=${DEBUG} \
  --log_file=${LOG_FILE} \
  --log_level=${LOG_LEVEL}
