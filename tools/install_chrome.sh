#!/bin/bash

readonly CHROME_DEB=/tmp/google-chrome-stable_current_amd64.deb

wget -O "${CHROME_DEB}" \
  "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb"
sudo dpkg -i "${CHROME_DEB}"
if [ $? -ne 0 ]; then
  sudo apt-get install -f
  sudo dpkg -i "${CHROME_DEB}"
fi
