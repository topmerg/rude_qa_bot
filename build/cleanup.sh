#!/bin/sh
set -e

pip --no-cache-dir \
    --disable-pip-version-check \
    --no-color \
    uninstall --yes --requirement build/requirements.txt

rm -rf /opt/app/*
