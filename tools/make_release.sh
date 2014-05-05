#!/bin/bash
#
# Used internally to make a zipped binary package for release.
# Run this script from a clean clone. Otherwise intermediate files like *.pyc
# or .cache/ directories are included in the release package.

KCAA_DIR=$(readlink -f $(dirname $0)/..)
BIN_DIR=${KCAA_DIR}/bin
CLIENT_DEPLOYED_DIR=${KCAA_DIR}/client_deployed

BROWSERMOB_PROXY_DIR=${HOME}/browsermob-proxy
PHANTOMJS_BINARY=${HOME}/phantomjs--linux-x86_64.tar.bz2
OUTPUT_DIR=${HOME}/kcaa_releases
TMP_DIR=$(mktemp -d)

function check_dir_name() {
  basename ${KCAA_DIR} | grep 'kcaa_v[0-9.]\+' &> /dev/null
  if [ $? -ne 0 ]; then
    echo "You are running this script within a non-versioned directory."
    echo "This is usually not what you want; the client directory will be" \
      "deleted, and furthermore the release package will contain a"\
      "non-versioned directory at the top level."
    echo "Aborting."
    exit 1
  fi
}

function check_bin_dir() {
  echo "Checking bin directory..."
  [ -d ${BIN_DIR} ] && rm -r ${BIN_DIR}
  mkdir ${BIN_DIR}
  [ -d ${CLIENT_DEPLOYED_DIR} ] && rm -r ${CLIENT_DEPLOYED_DIR}
  mkdir ${CLIENT_DEPLOYED_DIR}
}

function prepare_browsermob_proxy() {
  echo "Preparing BrowserMob Proxy..."
  unzip -q \
    -d ${BIN_DIR} \
    ${BROWSERMOB_PROXY_DIR}/target/browsermob-proxy-*-bin.zip
  mv ${BIN_DIR}/browsermob-proxy-* ${BIN_DIR}/browsermob-proxy
  # Shorten the CLASSPATH in the startup script for Windows with wild card.
  # It's very likely to exceed the byte size limit of environment variables.
  local run_script_win=${BIN_DIR}/browsermob-proxy/bin/browsermob-proxy.bat
  grep '^set CLASSPATH="%BASEDIR%"\\etc;"%REPO%"' \
    ${run_script_win} &> /dev/null
  if [ $? -ne 0 ]; then
    echo "CLASSPATH setting not found in Windows startup script. Fix the" \
      "pattern and rerun."
    exit 1
  fi
  # Do not forget to put \r to the end, as the line ending of this file is
  # CR+LF.
  sed -e 's/^\(set CLASSPATH="%BASEDIR%"\\etc;"%REPO%"\).*$/\1\\*\r/' \
    ${run_script_win} > ${TMP_DIR}/run_script_win
  cp ${TMP_DIR}/run_script_win ${run_script_win}
}

function prepare_chromedriver() {
  echo "Preparing Chromedriver..."
  local storage_base='http://chromedriver.storage.googleapis.com'
  local latest_version=$(wget -4 -q -O - ${storage_base}/LATEST_RELEASE)
  echo "Chromedriver's latest version is ${latest_version}."
  local filenames=(
    chromedriver_linux64.zip
    chromedriver_win32.zip
  )
  for filename in ${filenames[@]}
  do
    echo "Preparing ${filename}..."
    wget -4 -q -O ${TMP_DIR}/${filename} \
      ${storage_base}/${latest_version}/${filename}
    unzip -q -d ${BIN_DIR} ${TMP_DIR}/${filename}
  done
}

function prepare_phantomjs() {
  echo "Preparing PhantomJS..."
  tar xf ${PHANTOMJS_BINARY} --directory=${BIN_DIR}
}

function prepare_get_pip() {
  echo "Preparing get-pip.py..."
  local get_pip=https://bootstrap.pypa.io/get-pip.py
  wget -4 -q -O ${BIN_DIR}/get-pip.py ${get_pip}
}

function build_client() {
  echo "Building KCAA client..."
  pushd ${KCAA_DIR}/client
  pub build
  mv build ${CLIENT_DEPLOYED_DIR}
  popd
  # Remove the client directory as it contains packages symblic links.
  # Also it's not required for a release package.
  rm -r ${KCAA_DIR}/client
}

function copy_licenses() {
  echo "Copying license file..."
  cp ${KCAA_DIR}/thirdparty.txt ${BIN_DIR}
}

function copy_version_file() {
  echo "Copying version file..."
  cp ${KCAA_DIR}/BINARY_VERSION ${BIN_DIR}
  cp ${KCAA_DIR}/CLIENT_VERSION ${CLIENT_DEPLOYED_DIR}
}

function move_old_package() {
  local filename=$1
  if [ -e ${filename} ]; then
    local tmp=$(mktemp)
    mv ${filename} ${tmp}
    echo "${filename} already exists. Moved to ${tmp}."
  fi
}

function zip_package() {
  echo "Zipping KCAA binary package..."
  pushd ${KCAA_DIR}
  local binary_version=$(head -n 1 BINARY_VERSION | cut -d , -f 1)
  local kcaa_bin=${OUTPUT_DIR}/kcaa_bin_${binary_version}.zip
  move_old_package ${kcaa_bin}
  zip -q -r ${kcaa_bin} $(basename ${BIN_DIR})
  echo "Zipping KCAA deployed client package..."
  local client_version=$(head -n 1 CLIENT_VERSION | cut -d , -f 1)
  local kcaa_client=${OUTPUT_DIR}/kcaa_client_${client_version}.zip
  move_old_package ${kcaa_client}
  zip -q -r ${kcaa_client} $(basename ${CLIENT_DEPLOYED_DIR})
  cd ${KCAA_DIR}/..
  echo "Zippping KCAA release package..."
  local kcaa_release=${OUTPUT_DIR}/kcaa_release_${client_version}.zip
  move_old_package ${kcaa_release}
  local kcaa_basename=$(basename ${KCAA_DIR})
  zip -q -r ${kcaa_release} ${kcaa_basename} -x \
    ${kcaa_basename}/.git/ \
    ${kcaa_basename}/.git/**\* \
    ${kcaa_basename}/.*
  popd
}

check_dir_name
check_bin_dir
prepare_browsermob_proxy
prepare_chromedriver
#prepare_phantomjs
prepare_get_pip
build_client
copy_licenses
copy_version_file
zip_package

rm -r ${TMP_DIR}
