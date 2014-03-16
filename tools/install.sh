#!/bin/bash

SCRIPT_DIR=$(dirname $0)
source ${SCRIPT_DIR}/config

THIRDPARTY_DIR=${SCRIPT_DIR}/../thirdparty

function confirm_install_prerequisites() {
  local -A prerequisites=(
    ["gcc"]="gcc"
    ["pip"]="python-pip"
    ["tar"]="tar"
    ["unzip"]="unzip"
  )
  which apt-get &> /dev/null
  if [ $? -ne 0 ]; then
    echo "Cannot find 'apt-get' (APT package manager)."
    echo "Possibly you are not using Debian-originated Linux?"
    echo "TODO: Support non-Debian Linux distributions."
    exit 1
  fi
  for command in ${!prerequisites[@]}
  do
    which ${command} &> /dev/null
    if [ $? -ne 0 ]; then
      echo "Cannot find '${command}'."
      echo "Possibly you can install it by 'sudo apt-get install" \
        "${prerequisites[${command}]}'."
      exit 1
    fi
  done
}

function create_install_directory() {
  echo "Creating INSTALL_DIR: ${INSTALL_DIR}"
  mkdir -p ${INSTALL_DIR}
  if [ $? -ne 0 ]; then
    echo "Failed to create the install path: ${INSTALL_DIR}"
    exit 1
  fi
}

function install_kancolle_player_prerequisites() {
  local kancolle_player_prerequisites=(
    flashplugin-installer
    xorg
  )
  echo "Installing Kancolle player prerequisites..."
  sudo apt-get install ${kancolle_player_prerequisites[@]}
}

# Python third-party packages required to run the KCAA Python server.
function install_python_server_prerequisites() {
  local python_server_apt_prerequisites=(
    openjdk-7-jre
    python-dev
    zlib1g-dev
  )
  echo "Installing KCAA Python server APT prerequisites..."
  sudo apt-get install ${python_server_apt_prerequisites[@]}
  local python_server_prerequisites=(
    pillow
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

function install_phantomjs() {
  if [ -x ${INSTALL_DIR}/phantomjs ]; then
    echo "PhantomJS is already installed at ${INSTALL_DIR}/phantomjs. " \
      "Skipping."
    return
  fi

  echo "Installing PhantomJS..."
  local filename=phantomjs--linux-x86_64
  tar xf ${THIRDPARTY_DIR}/${filename}.tar.bz2 --directory=${INSTALL_DIR}
  ln -s ${INSTALL_DIR}/${filename}/bin/phantomjs ${INSTALL_DIR}/phantomjs
}

function install_browsermob_proxy() {
  if [ -d ${INSTALL_DIR}/browsermob-proxy ]; then
    echo "Browsermob Proxy is already installed at " \
      "${INSTALL_DIR}/browsermob-proxy. Skipping."
    return
  fi

  echo "Installing Browsermob Proxy..."
  local filename=browsermob-proxy-2.0-beta-10-SNAPSHOT
  unzip -q -d ${INSTALL_DIR} ${THIRDPARTY_DIR}/${filename}-bin.zip
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
install_kancolle_player_prerequisites
install_python_server_prerequisites
install_chromedriver
install_phantomjs
install_browsermob_proxy
install_dartium

echo "Installation finished."
