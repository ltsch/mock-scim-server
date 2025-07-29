#!/bin/bash
# Wrapper script to run SCIM server with virtual environment

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if virtual environment exists
if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Error: Virtual environment not found at $SCRIPT_DIR/.venv"
    echo "Please create it with: python3 -m venv .venv"
    echo "Then install dependencies with: source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Error: Failed to activate virtual environment"
    exit 1
fi

echo "Using virtual environment: $VIRTUAL_ENV"
echo "Python executable: $(which python)"

# Run the server script with all arguments passed through
exec python "$SCRIPT_DIR/run_server.py" "$@"