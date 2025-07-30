#!/bin/bash
set -e

echo "Starting SCIM Server..."

# Create database directory if it doesn't exist
mkdir -p /app/db

# Initialize database if it doesn't exist
if [ ! -f /app/db/scim.db ]; then
    echo "Initializing database..."
    python scripts/init_db.py
    echo "Database initialized successfully"
else
    echo "Database already exists, skipping initialization"
fi

# Start the server
echo "Starting uvicorn server..."
exec uvicorn scim_server.main:app --host 0.0.0.0 --port 7001 