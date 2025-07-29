#!/bin/bash
# Script to copy necessary files for local Docker setup

# Configuration
REMOTE_HOST="your-remote-host"
REMOTE_USER="your-username"
REMOTE_PATH="~/scim-server"
LOCAL_PATH="./local-scim-server"

echo "🚀 Setting up SCIM Server for local Docker..."

# Create local directory
mkdir -p "$LOCAL_PATH"

# Copy necessary files
echo "📁 Copying Docker files..."
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/Dockerfile" "$LOCAL_PATH/"
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/docker-compose.yml" "$LOCAL_PATH/"
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/requirements.txt" "$LOCAL_PATH/"
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/DOCKER.md" "$LOCAL_PATH/"

echo "📁 Copying application code..."
scp -r "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/scim_server/" "$LOCAL_PATH/"

echo "📁 Copying additional files..."
scp "$REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/.dockerignore" "$LOCAL_PATH/" 2>/dev/null || echo "No .dockerignore found"

echo "✅ Files copied successfully!"
echo ""
echo "🎯 Next steps:"
echo "1. cd $LOCAL_PATH"
echo "2. docker compose up --build"
echo ""
echo "📖 For more information, see DOCKER.md" 