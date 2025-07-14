#!/usr/bin/env bash
# This script runs the tests for the project.
set -e
# Check if the script is run from the root directory
if [ ! -f "run_tests.sh" ]; then
    echo "Please run this script from the root directory of the project."
    exit 1
fi

export PYTHONPATH=$(pwd)

# Run the tests
pytest --maxfail=1 --disable-warnings -q
# Check if the tests passed
if [ $? -eq 0 ]; then
    echo "All tests passed successfully."
else
    echo "Some tests failed. Please check the output above for details."
    exit 1
fi