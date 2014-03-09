#!/bin/bash

SCRIPT_DIR=$(dirname $0)
source ${SCRIPT_DIR}/config

function confirm_install_prerequisites() {
  which pip &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Cannot find 'pip' (Python package installer/manager)."
    echo "Possibly you can install it by 'sudo apt-get install python-pip'."
    exit 1
  fi
}

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
  unzip -q -d ${INSTALL_DIR} ${INSTALL_DIR}/${filename}
}

function install_browsermob_proxy() {
  if [ -d ${INSTALL_DIR}/browsermob-proxy ]; then
    echo "Browsermob Proxy is already installed at " \
      "${INSTALL_DIR}/browsermob-proxy. Skipping."
    return
  fi

  echo "Installing Browsermob Proxy..."
  local filename=browsermob-proxy-2.0-beta-10-SNAPSHOT
  unzip -q -d ${INSTALL_DIR} ${SCRIPT_DIR}/../thirdparty/${filename}-bin.zip
  ln -s ${INSTALL_DIR}/${filename} ${INSTALL_DIR}/browsermob-proxy
}

function install_dartium() {
  if [ -d ${INSTALL_DIR}/dartium ]; then
    echo "Dartium is already installed at ${INSTALL_DIR}/dartium. Skipping."
    return
  fi

  local storage_base='http://storage.googleapis.com/dart-archive/channels/'\
'stable/release/latest/dartium'
  local filename='dartium-linux-x64-release.zip'
  echo "Installing the latest Dartium..."
  wget -q -O ${INSTALL_DIR}/${filename} ${storage_base}/${filename}
  echo "Unzipping..."
  unzip -q -d ${INSTALL_DIR} ${INSTALL_DIR}/${filename}
  local dart_dir=$(unzip -l -qq ${INSTALL_DIR}/${filename} \
    | awk '{print $NF}' \
    | head -n 1 \
    | sed -e 's|/$||')
  ln -s ${INSTALL_DIR}/${dart_dir} ${INSTALL_DIR}/dartium
}

confirm_install_prerequisites
create_install_directory
install_python_server_prerequisites
install_chromedriver
install_browsermob_proxy
install_dartium

echo "Installation finished."
