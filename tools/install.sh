#!/bin/bash

SCRIPT_DIR=$(dirname $0)
source ${SCRIPT_DIR}/config

function confirm_install_prerequisites() {
  local -A prerequisites=(
    ["gcc"]="gcc"
    ["pip"]="python-pip"
    ["unzip"]="unzip"
    ["wget"]="wget"
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

function create_user_data_directory() {
  echo "Creating USER_DATA_DIR: ${USER_DATA_DIR} with mode 700"
  mkdir -p ${USER_DATA_DIR} -m 700
  if [ $? -ne 0 ]; then
    echo "Failed to create the user data path: ${USER_DATA_DIR}"
    exit 1
  fi
}

function install_kancolle_player_prerequisites() {
  local kancolle_player_prerequisites=(
    flashplugin-installer
    fonts-ipafont-gothic
    xorg
  )
  echo "Installing Kancolle player prerequisites..."
  sudo apt-get install ${kancolle_player_prerequisites[@]}
}

# Python third-party packages required to run the KCAA Python server.
function install_python_server_prerequisites() {
  local python_server_apt_prerequisites=(
    libjpeg8-dev
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
    "--find-links https://code.google.com/p/google-visualization-python/ gviz-api-py"
  )
  echo "Installing KCAA Python server prerequisites..."
  for package in "${python_server_prerequisites[@]}"
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

function install_phantomjs() {
  # PhantomJS requires some shared libraries to run.
  local phantomjs_apt_prerequisites=(
    python-pyphantomjs
  )
  echo "Installing PhantomJS APT prerequisites..."
  sudo apt-get install ${phantomjs_apt_prerequisites[@]}
}

function install_dartium() {
  if [ -d ${BIN_DIR}/dartium ]; then
    echo "Dartium is already installed at ${BIN_DIR}/dartium. Skipping."
    return
  fi

  local storage_base='http://storage.googleapis.com/dart-archive/channels/'\
'stable/release/latest/dartium'
  local filename='dartium-linux-x64-release.zip'
  echo "Installing the latest Dartium..."
  wget -q -O ${BIN_DIR}/${filename} ${storage_base}/${filename}
  echo "Unzipping..."
  unzip -q -d ${BIN_DIR} ${BIN_DIR}/${filename}
  local dart_dir=$(unzip -l -qq ${BIN_DIR}/${filename} \
    | awk '{print $NF}' \
    | head -n 1 \
    | sed -e 's|/$||')
  ln -s ${BIN_DIR}/${dart_dir} ${BIN_DIR}/dartium
}

confirm_install_prerequisites
create_user_data_directory
install_kancolle_player_prerequisites
install_python_server_prerequisites
#install_phantomjs
#install_dartium

UPDATE_REPOSITORY=0 ${SCRIPT_DIR}/update.sh

echo "Installation finished."
