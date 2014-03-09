#!/bin/bash

# Python third-party packages required to run the KCAA Python server.
function install_python_server_prerequisites() {
  local python_server_prerequisites=(
    python-dateutil
    requests
    selenium
  )
  for package in ${python_server_prerequisites[@]}
  do
    pip install ${package}
  done
}

# Python packages required to test the KCAA Python server code.
function install_python_server_testing_prerequisites() {
  local python_server_prerequisites=(
    pytest
    pytest-cov
    pytest-pep8
  )
  for package in ${python_server_testing_prerequisites[@]}
  do
    pip install ${package}
  done
}

install_python_server_prerequisites
