# Docker Setup for SCIM Server

This repository includes Docker configuration to run the SCIM server in a containerized environment.

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Build and start the container:**
   ```bash
   docker-compose up --build
   ```

2. **Run in background:**
   ```bash
   docker-compose up -d --build
   ```

3. **Stop the container:**
   ```bash
   docker-compose down
   ```

## Configuration

### Environment Variables

The following environment variables can be configured in `docker-compose.yml`:

- `PYTHONPATH`: Set to `/app` (default)
- `LOG_LEVEL`: Set to `info` (default)
- `DATABASE_URL`: Set to `sqlite:////app/db/scim.db` (default)

### Volumes

The following volumes are configured for persistence:

- `scim_database` → `/app/db` (main database - Docker volume)
- `./logs` → `/app/logs` (application logs - bind mount)

**Database Volume**: The `scim_database` volume is a Docker-managed volume that persists across container restarts and reboots. This ensures your SCIM server data is preserved even when containers are recreated.

### Ports

- `7001` - Main SCIM server port

## Database Persistence

### Docker Volume Benefits

- **Persistent Storage**: Database survives container restarts and reboots
- **Isolated Storage**: Database is managed by Docker and isolated from host filesystem
- **Easy Backup**: Volume can be easily backed up using Docker commands
- **Performance**: Better I/O performance compared to bind mounts

### Managing the Database Volume

**List volumes:**
```bash
docker volume ls
```

**Inspect volume details:**
```bash
docker volume inspect scim_database
```

**Backup the database:**
```bash
docker run --rm -v scim_database:/data -v $(pwd):/backup alpine tar czf /backup/scim_database_backup.tar.gz -C /data .
```

**Restore the database:**
```bash
docker run --rm -v scim_database:/data -v $(pwd):/backup alpine tar xzf /backup/scim_database_backup.tar.gz -C /data
```

**Remove the volume (WARNING: This will delete all data):**
```bash
docker volume rm scim_database
```

## Health Checks

The container includes robust health checks that verify the application is running properly:

### Basic Health Check
```bash
curl http://localhost:7001/healthz
```
Returns: `{"status": "ok", "timestamp": "..."}`

**Access**: Public - accessible from any network

### Detailed Health Check
```bash
curl http://localhost:7001/health
```
Returns comprehensive health information including database status.

**Access**: Internal networks only - restricted to:
- Localhost (127.0.0.1, ::1)
- Private networks (RFC 1918: 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16)
- Docker networks (172.16.0.0/12, 192.168.0.0/16)
- Link-local addresses (169.254.0.0/16, fe80::/10)

**Security**: The `/health` endpoint is restricted to internal networks for security, while `/healthz` remains publicly accessible for load balancers and external monitoring.

### Health Check Configuration

- **Start Period**: 60 seconds (allows time for application startup)
- **Interval**: 30 seconds (how often to check)
- **Timeout**: 10 seconds (timeout for each check)
- **Retries**: 5 (number of failures before marking unhealthy)

**Note**: Health check endpoints do not require authentication and are designed for Docker health monitoring.

## Development

### Building the Image

```bash
docker build -t scim-server .
```

### Running the Container

```bash
docker run -p 7001:7001 -v scim_database:/app/db -v $(pwd)/logs:/app/logs scim-server
```

### Viewing Logs

```bash
# Docker Compose logs
docker-compose logs -f scim-server

# Direct container logs
docker logs -f scim-server
```

### Database Initialization

The container automatically initializes the database on first startup. The startup script (`start.sh`) checks if the database file exists and initializes it if needed.

**Manual database initialization:**
```bash
docker exec scim-server python scripts/init_db.py
```

### CLI Access

Access the SCIM CLI from within the container:

```bash
# List all servers
docker exec scim-server python scripts/scim_cli.py list

# Create a new server
docker exec scim-server python scripts/scim_cli.py create --app-profile hr --defaults

# Create server with specific ID
docker exec scim-server python scripts/scim_cli.py create --server-id your-server-id --app-profile hr --defaults
```

## Troubleshooting

### Database Issues

**Check if database exists:**
```bash
docker exec scim-server ls -la /app/db/
```

**Check database contents:**
```bash
docker exec scim-server python -c "import sqlite3; conn = sqlite3.connect('/app/db/scim.db'); cursor = conn.cursor(); cursor.execute('SELECT COUNT(*) FROM users'); print('Users:', cursor.fetchone()[0]); conn.close()"
```

**Reset database (WARNING: This will delete all data):**
```bash
docker exec scim-server python scripts/scim_cli.py reset
```

### Volume Issues

**Check volume status:**
```bash
docker volume ls | grep scim_database
```

**Inspect volume:**
```bash
docker volume inspect scim_database
```

**Recreate volume (WARNING: This will delete all data):**
```bash
docker-compose down
docker volume rm scim_database
docker-compose up --build
```

## Production Considerations

### Security

- The container runs as root for simplicity, but you can modify the Dockerfile to run as a non-root user
- Database volume is isolated from the host filesystem
- Health checks are available for monitoring

### Backup Strategy

1. **Regular backups**: Set up automated backups of the `scim_database` volume
2. **Test restores**: Regularly test backup restoration procedures
3. **Multiple locations**: Store backups in multiple locations

### Monitoring

- Use the health check endpoints for monitoring
- Monitor container logs for errors
- Set up alerts for database connectivity issues

### Scaling

- The current setup is designed for single-instance deployment
- For multi-instance deployment, consider using an external database (PostgreSQL, MySQL)
- Update the `DATABASE_URL` environment variable to point to your external database