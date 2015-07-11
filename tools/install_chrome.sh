#!/bin/bash

# TODO: If this list is updated so often, consider extract using `dpkg -I`
readonly PREREQUISITES=(
  libpango1.0-0
  libxss1
  libappindicator1
  xdg-utils
)
readonly CHROME_DEB=/tmp/google-chrome-stable_current_amd64.deb

wget -O "${CHROME_DEB}" \
  "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
sudo apt-get install "${PREREQUISITES[@]}"
sudo dpkg -i "${CHROME_DEB}"
