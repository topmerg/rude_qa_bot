#!/bin/sh
set -e

if [ -z "${1}" ]; then
    echo "Usage: ${0} DIRNAME"
    exit 1
fi

if [ -e "${1}" ]; then
    echo "Linting source dir: ${1} ..."
else
    echo "Source dir not found: ${1}"
    exit 1
fi

pylint --errors-only "${1}"

echo "Done."
