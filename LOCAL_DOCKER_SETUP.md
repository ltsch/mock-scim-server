# Local Docker Setup Guide

This guide helps you run the SCIM server Docker containers on your local machine using Docker Desktop.

## Prerequisites

- Docker Desktop installed and running on your local machine
- SSH access to the remote server (if copying files)
- Git (if cloning from repository)

## Quick Start

### Option 1: Copy Files from Remote Server

1. **Edit the copy script** (if needed):
   ```bash
   # Edit the script to match your remote server details
   nano copy-for-local-docker.sh
   ```

2. **Run the copy script**:
   ```bash
   ./copy-for-local-docker.sh
   ```

3. **Build and run the containers**:
   ```bash
   cd local-scim-server
   docker compose up --build
   ```

### Option 2: Manual Copy

If you prefer to copy files manually:

```bash
# Create local directory
mkdir local-scim-server
cd local-scim-server

# Copy files from remote server (replace with your details)
scp user@remote-host:~/scim-server/Dockerfile .
scp user@remote-host:~/scim-server/docker-compose.yml .
scp user@remote-host:~/scim-server/requirements.txt .
scp -r user@remote-host:~/scim-server/scim_server/ .
scp user@remote-host:~/scim-server/.dockerignore .

# Build and run
docker compose up --build
```

### Option 3: Git Clone

If the repository is on GitHub:

```bash
git clone <repository-url> local-scim-server
cd local-scim-server
docker compose up --build
```

## Verify It's Working

Once the containers are running:

1. **Check health endpoint** (public access):
   ```bash
   curl http://localhost:7001/healthz
   ```

2. **Check detailed health** (from localhost):
   ```bash
   curl http://localhost:7001/health
   ```

3. **Test SCIM endpoint** (requires API key):
   ```bash
   curl -H "Authorization: Bearer api-key-12345" \
        http://localhost:7001/scim-identifier/test-server/scim/v2/ResourceTypes
   ```

## Troubleshooting

### Port Already in Use
If port 7001 is already in use:
```bash
# Edit docker-compose.yml to use a different port
# Change "7001:7001" to "8080:7001" for example
docker compose up --build
```

### Permission Issues
If you get permission errors:
```bash
# Make sure Docker Desktop is running
# Check Docker Desktop status in your system tray
```

### Build Issues
If the build fails:
```bash
# Clean up and rebuild
docker compose down
docker system prune -f
docker compose up --build
```

## Next Steps

- Read `DOCKER.md` for detailed Docker documentation
- Check `README.md` for comprehensive SCIM server documentation
- Explore the API endpoints at `http://localhost:7001`

## Stopping the Containers

```bash
# Stop containers
docker compose down

# Stop and remove volumes (will delete database)
docker compose down -v
``` 