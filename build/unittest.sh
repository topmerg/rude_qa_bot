#!/bin/sh
set -e

set -- tests/*/*_test.py
if [ -f "$1" ]; then
    echo "Starting unittests..."
else
    echo "Unittests not found, skipping."
    exit 0
fi

python -m unittest discover -s tests -p "*_test.py"

echo "Done."
