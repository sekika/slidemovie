#!/bin/sh
# Change to this directory
cd `echo $0 | sed -e 's/[^/]*$//'`
cd ..
pytest

# Make package
python3 -m pip install build twine
echo "Making packages."
python3 -m build

# Token required. Check ~/.pypirc
twine upload --skip-existing dist/*
