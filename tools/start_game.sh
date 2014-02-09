#!/bin/bash

source $(dirname $0)/config

SERVER_BIN=$(dirname $0)/../server/server_main.py

${SERVER_BIN} \
  --browser=${BROWSER} \
  --chrome_binary=${CHROME_BIN} \
  --chromedriver_binary=${CHROMEDRIVER_BIN}

