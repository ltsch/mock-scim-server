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

### Volumes

The following directories are mounted for persistence:

- `./scim.db` → `/app/scim.db` (main database)
- `./logs` → `/app/logs` (application logs)
- `./test_scim.db` → `/app/test_scim.db` (test database)

### Ports

- `7001` - Main SCIM server port

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
docker run -p 7001:7001 -v $(pwd)/scim.db:/app/scim.db -v $(pwd)/logs:/app/logs scim-server
```

### Viewing Logs

```bash
# Docker Compose logs
docker-compose logs -f

# Direct container logs
docker logs scim-server
```

### Checking Health Status

```bash
# Check container health status
docker ps

# Check health check logs
docker inspect scim-server | grep -A 10 "Health"
```

## API Endpoints

Once running, the SCIM server will be available at:

- Health Check: `http://localhost:7001/healthz`
- Detailed Health: `http://localhost:7001/health`
- SCIM Endpoints: `http://localhost:7001/scim-identifier/{server_id}/scim/v2/`

## Troubleshooting

### Container Won't Start

1. Check if port 7001 is already in use:
   ```bash
   lsof -i :7001
   ```

2. Check container logs:
   ```bash
   docker-compose logs
   ```

3. Check health check status:
   ```bash
   docker ps
   docker inspect scim-server
   ```

### Health Check Failures

If health checks are failing:

1. Check if the application is starting properly:
   ```bash
   docker-compose logs scim-server
   ```

2. Test the health endpoint manually:
   ```bash
   curl http://localhost:7001/healthz
   curl http://localhost:7001/health
   ```

3. Verify the container is running:
   ```bash
   docker exec scim-server ps aux
   ```

### IP Restriction Issues

If you're getting "Access denied from external network" errors when accessing `/health`:

1. **From Docker container**: The `/health` endpoint is restricted to internal networks only
2. **From host machine**: Use `localhost` or `127.0.0.1` to access the endpoint
3. **From external networks**: Use `/healthz` instead, which is publicly accessible
4. **For monitoring systems**: Configure your monitoring to use `/healthz` for external checks

**Allowed networks for `/health`**:
- Localhost: `127.0.0.1`, `::1`
- Private networks: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`
- Docker networks: `172.16.0.0/12`, `192.168.0.0/16`
- Link-local: `169.254.0.0/16`, `fe80::/10`

### Database Issues

If you encounter database issues, you can reset the database:

1. Stop the container:
   ```bash
   docker-compose down
   ```

2. Remove the database file:
   ```bash
   rm scim.db
   ```

3. Restart the container:
   ```bash
   docker-compose up --build
   ```

### Permission Issues

If you encounter permission issues with mounted volumes, ensure the current user has write permissions to the mounted directories.

## Production Considerations

For production deployment:

1. Use environment-specific configuration
2. Consider using PostgreSQL instead of SQLite
3. Set up proper logging and monitoring
4. Configure SSL/TLS termination
5. Use secrets management for API keys
6. Monitor health check metrics
7. Set up alerting for health check failures