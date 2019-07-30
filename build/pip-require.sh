#!/bin/sh
set -e

if [ -z "${1}" ]; then
    echo "Usage: ${0} FILENAME"
    exit 1
fi

if [ -e "${1}" ]; then
    echo "Installing requirements: ${1} ..."
else
    echo "Requirements file not found: ${1}"
    exit 1
fi

pip --no-cache-dir \
    --disable-pip-version-check \
    --no-color install \
    --requirement "${1}"

echo "Cleaning up..."
find /usr/local/lib/python3.7 -name '*.c' -delete
find /usr/local/lib/python3.7 -name '*.pxd' -delete
find /usr/local/lib/python3.7 -name '*.pyd' -delete
find /usr/local/lib/python3.7 -name '__pycache__' | xargs rm -r

echo "Done."
