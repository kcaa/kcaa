#!/bin/bash

KCAA_DIR=$(readlink -f $(dirname $0)/..)

TMP_DIR=$(mktemp -d)

function update_binary() {
  local version_file=$1
  local target_dir=$2

  local current_version=$(head -n 1 ${target_dir}/${version_file} | cut -d , -f 1)
  local kcaa_repo_base=https://raw.githubusercontent.com/kcaa/kcaa
  local latest_version_file=${kcaa_repo_base}/latest_release/${version_file}
  wget -q -O ${TMP_DIR}/${version_file} ${latest_version_file}
  local latest_version=$(head -n 1 ${TMP_DIR}/${version_file} | cut -d , -f 1)
  if [ ${current_version} = ${latest_version} ]; then
    echo "${target_dir} is up to date. (${latest_version})"
    return
  fi
  # Download and update the target directory.
  echo "Renaming the existing ${target_dir} to" \
    "${target_dir}_${current_version}..."
  mv ${target_dir} ${target_dir}_${current_version}
  echo "Downloading the latest ${target_dir} package of ${latest_version}..."
  local latest_package=$(head -n 1 ${TMP_DIR}/${version_file} | cut -d , -f 2)
  wget -q -O ${TMP_DIR}/${target_dir}.zip ${latest_package}
  unzip -q -d ${KCAA_DIR} ${TMP_DIR}/${target_dir}.zip
  echo "Updated ${target_dir} to ${latest_version}."
}

cd ${KCAA_DIR}

update BINARY_VERSION bin
update CLIENT_VERSION client_deployed

rm -rf ${TMP_DIR}

echo "Update finished."
