#!/bin/bash
#
# Convenience wrapper for running the BMW dealership scraper
# This script activates the virtual environment and runs the scraper
#

set -e

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please create it first with: python3 -m venv .venv"
    exit 1
fi

# Run the scraper with all arguments passed through
"$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/run_scraper.py" "$@"
