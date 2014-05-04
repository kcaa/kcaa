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
zip_package

rm -r ${TMP_DIR}
