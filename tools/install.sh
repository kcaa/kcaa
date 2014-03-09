#!/bin/bash

SCRIPT_DIR=$(dirname $0)
source ${SCRIPT_DIR}/config

function create_install_directory() {
  echo "Creating INSTALL_DIR: ${INSTALL_DIR}"
  mkdir -p ${INSTALL_DIR}
  if [ $? -ne 0 ]; then
    echo "Failed to create the install path: ${INSTALL_DIR}"
    exit 1
  fi
}

# Python third-party packages required to run the KCAA Python server.
function install_python_server_prerequisites() {
  local python_server_prerequisites=(
    python-dateutil
    requests
    selenium
  )
  echo "Installing KCAA Python server prerequisites..."
  for package in ${python_server_prerequisites[@]}
  do
    sudo pip install ${package}
  done
}

# Python packages required to test the KCAA Python server code.
function install_python_server_testing_prerequisites() {
  local python_server_prerequisites=(
    pytest
    pytest-cov
    pytest-pep8
  )
  echo "Installing KCAA Python server testing prerequisites..."
  for package in ${python_server_testing_prerequisites[@]}
  do
    sudo pip install ${package}
  done
}

function install_chromedriver() {
  if [ -x ${INSTALL_DIR}/chromedriver ]; then
    echo "Chromedrive is already installed at ${INSTALL_DIR}/chromedriver." \
      "Skipping."
    return
  fi

  local storage_base='http://chromedriver.storage.googleapis.com'
  local filename='chromedriver_linux64.zip'
  echo "Installing the latest Chromedriver..."
  local latest_version=$(wget -q -O - ${storage_base}/LATEST_RELEASE)
  echo "Latest version of Chromedriver is ${latest_version}. Downloading..."
  wget -q -O ${INSTALL_DIR}/${filename} \
    ${storage_base}/${latest_version}/${filename}
  echo "Unzipping..."
  unzip -d ${INSTALL_DIR} ${INSTALL_DIR}/${filename}
}

function install_browsermob_proxy() {
  if [ -x ${INSTALL_DIR}/browsermob-proxy ]; then
    echo "Browsermob Proxy is already installed at " \
      "${INSTALL_DIR}/browsermob-proxy. Skipping."
    return
  fi

  echo "Installing Browsermob Proxy..."
  cp -f ${SCRIPT_DIR}/../thirdparty/browsermob-proxy ${INSTALL_DIR}
}

create_install_directory
install_python_server_prerequisites
install_chromedriver
install_browsermob_proxy
