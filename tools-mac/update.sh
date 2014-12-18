#!/bin/bash

# Tricky -- no easy tool to canonicalize the path in Mac OS.
KCAA_DIR=$(cd $(dirname $0)/..; pwd)
UPDATE_REPOSITORY=${UPDATE_REPOSITORY-1}

TMP_DIR=$(mktemp -d /tmp/tmp.XXXXXXXX)

function update_repository() {
  if ((UPDATE_REPOSITORY == 0)); then
    return
  fi
  if [ ! -d .git ]; then
    echo "No git repository found; you must have installed via a release" \
      "package."
    echo "In place update is not possible without git repository, as the" \
      "server code will be inconsistent with client code. Aborting."
    echo "If you want to enable in place update from next time, try git " \
      "clone:"
    echo "  cd ~"
    echo "  git clone https://github.com/kcaa/kcaa.git"
    echo "  cd kcaa"
    echo "  tools/update.sh"
    exit 1
  fi
  echo "Updating git repository..."
  git fetch origin
  git merge origin/latest_release
  echo "Successfully updated git repository."
}

function update() {
  local version_file=$1
  local target_dir=$2

  local current_version=v0.0.0
  if [ -r ${target_dir}/${version_file} ]; then
    current_version=$(head -n 1 ${target_dir}/${version_file} | cut -d , -f 1)
  fi
  local kcaa_repo_base=https://raw.githubusercontent.com/kcaa/kcaa
  local latest_version_file=${kcaa_repo_base}/latest_release/${version_file}
  curl -sL ${latest_version_file} > ${TMP_DIR}/${version_file}
  local latest_version=$(head -n 1 ${TMP_DIR}/${version_file} | cut -d , -f 1)
  if [ "${current_version}" = "${latest_version}" ]; then
    echo "${target_dir} is up to date. (${latest_version})"
    return
  fi
  # Download and update the target directory.
  if [ -d ${target_dir} ]; then
    echo "Renaming the existing ${target_dir} to" \
      "${target_dir}_${current_version}..."
    mv ${target_dir} ${target_dir}_${current_version}
  fi
  echo "Downloading the latest ${target_dir} package of ${latest_version}..."
  local latest_package=$(head -n 1 ${TMP_DIR}/${version_file} | cut -d , -f 2)
  curl -sL ${latest_package} > ${TMP_DIR}/${target_dir}.zip
  unzip -q -d ${KCAA_DIR} ${TMP_DIR}/${target_dir}.zip
  echo "Successfully updated ${target_dir} to ${latest_version}."
}

cd ${KCAA_DIR}

update_repository
update BINARY_VERSION bin
update CLIENT_VERSION client_deployed

rm -rf ${TMP_DIR}

echo "Update finished."
