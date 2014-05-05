#!/bin/bash
#
# Used internally to make a zipped binary package for release.
# Run this script from a clean clone. Otherwise intermediate files like *.pyc
# or .cache/ directories are included in the release package.

KCAA_DIR=$(readlink -f $(dirname $0)/..)
BIN_DIR=${KCAA_DIR}/bin

BROWSERMOB_PROXY_DIR=${HOME}/browsermob-proxy
PHANTOMJS_BINARY=${HOME}/phantomjs--linux-x86_64.tar.bz2
OUTPUT_DIR=${HOME}
TMP_DIR=$(mktemp -d)

function check_bin_dir() {
  echo "Checking bin directory..."
  if [ -d ${BIN_DIR} ]; then
    echo "Directory ${BIN_DIR} exists. Move or remove it before proceeding."
    exit 1
  fi
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
  mv build ${BIN_DIR}
  popd
}

function copy_licenses() {
  echo "Copying license file..."
  cp ${KCAA_DIR}/thirdparty.txt ${BIN_DIR}
}

function copy_version_file() {
  echo "Copying version file..."
  cp ${KCAA_DIR}/BINARY_VERSION ${BIN_DIR}
}

function zip_package() {
  echo "Zipping KCAA binary package..."
  pushd ${KCAA_DIR}
  local kcaa_bin=${OUTPUT_DIR}/kcaa_bin.zip
  if [ -e ${kcaa_bin} ]; then
    local kcaa_bin_tmp=$(mktemp)
    mv ${kcaa_bin} ${kcaa_bin_tmp}
    echo "${kcaa_bin} already exists. Moved to ${kcaa_bin_tmp}."
  fi
  zip -q -r ${kcaa_bin} bin
  cd ${KCAA_DIR}/..
  echo "Zippping KCAA release package..."
  local kcaa_release=${OUTPUT_DIR}/kcaa_release.zip
  if [ -e ${kcaa_release} ]; then
    local kcaa_release_tmp=$(mktemp)
    mv ${kcaa_release} ${kcaa_release_tmp}
    echo "${kcaa_release} already exists. Moved to ${kcaa_release_tmp}."
  fi
  zip -q -r ${kcaa_release} kcaa -x \
    kcaa/.git/ \
    kcaa/.git/**\* \
    kcaa/.*
  popd
}

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
