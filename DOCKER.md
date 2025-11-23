# Docker Deployment Guide

This guide explains how to deploy the Google Analytics MCP Server using Docker.

## Prerequisites

- Docker Engine 20.10 or higher
- Docker Compose 2.0 or higher
- Google Cloud OAuth credentials (see main README)

## Quick Start

1. **Configure Environment Variables**

   Create a `.env` file in the project root:
   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your Google OAuth credentials:
   ```bash
   FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider
   FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
   FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
   FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/analytics.readonly
   ```

2. **Build the Docker Image**

   ```bash
   make build
   ```

   Or manually:
   ```bash
   docker-compose build
   ```

3. **Start the Server**

   ```bash
   make up
   ```

   Or manually:
   ```bash
   docker-compose up -d
   ```

4. **Verify the Server is Running**

   ```bash
   make status
   ```

   Or manually:
   ```bash
   curl http://localhost:8000/health
   ```

## Docker Architecture

### Image Details

- **Base Image**: `python:3.12-slim`
- **Package Manager**: UV (for fast dependency installation)
- **Dependencies**: 
  - `fastmcp[google]` - FastMCP with Google OAuth support
  - `google-api-python-client` - Google API client library
  - `google-auth` - Google authentication library

### Container Configuration

- **Port**: 8000 (HTTP transport)
- **Health Check**: Every 30 seconds on `/health` endpoint
- **Restart Policy**: `unless-stopped`
- **Network**: Bridge network (`mcp-network`)

## Available Commands

All commands can be run using the Makefile:

### Building

```bash
# Build the Docker image
make build

# Rebuild from scratch
make rebuild
```

### Running

```bash
# Start server in background
make up

# Start server with live logs
make dev

# Stop server
make down

# Restart server
make restart
```

### Monitoring

```bash
# View live logs
make logs

# View last 100 lines
make logs-tail

# Check server status
make status

# Test health endpoint
make test
```

### Maintenance

```bash
# Open shell in container
make shell

# Clean up all resources
make clean
```

## Environment Variables

The following environment variables can be configured in `.env`:

### Required

- `FASTMCP_SERVER_AUTH` - Authentication provider class
- `FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID` - Google OAuth client ID
- `FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES` - Required OAuth scopes

### Optional

- `FASTMCP_SERVER_HOST` - Server host (default: `0.0.0.0`)
- `FASTMCP_SERVER_PORT` - Server port (default: `8000`)
- `FASTMCP_LOG_LEVEL` - Logging level (default: `INFO`)

## Health Checks

The server includes built-in health checks:

- **Endpoint**: `http://localhost:8000/health`
- **Interval**: 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3
- **Start Period**: 10 seconds

Health check response:
```json
{
  "status": "healthy",
  "server": "Google Analytics MCP",
  "version": "0.1.0"
}
```

## Networking

### Ports

- **8000**: HTTP transport for MCP protocol

### Accessing the Server

From host machine:
```bash
# Health check
curl http://localhost:8000/health

# MCP endpoint (requires authentication)
curl http://localhost:8000/mcp
```

From other containers (same network):
```bash
curl http://mcp-ga-server:8000/health
```

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
make logs
```

**Common issues:**
- Missing `.env` file
- Invalid OAuth credentials
- Port 8000 already in use

**Solution:**
```bash
# Check if port is in use
lsof -i :8000

# Use different port
# Edit docker-compose.yml and change port mapping
ports:
  - "8080:8000"  # Map host port 8080 to container port 8000
```

### Health Check Failing

**Check container status:**
```bash
docker-compose ps
```

**View detailed logs:**
```bash
make logs-tail
```

**Common causes:**
- Server not fully started (wait 10-15 seconds)
- Python dependencies missing
- Configuration errors

**Solution:**
```bash
# Rebuild container
make rebuild
```

### Authentication Issues

**Problem**: OAuth redirect not working

**Solution:**
- Ensure redirect URI in Google Cloud Console is `http://localhost:8000/auth/callback`
- If using different port, update redirect URI accordingly
- Check that OAuth credentials in `.env` are correct

### Permission Denied

**Problem**: Container can't access files

**Solution:**
```bash
# Fix file permissions
chmod -R 755 src/
```

### Out of Memory

**Problem**: Container crashes due to memory

**Solution:**
Add memory limits to `docker-compose.yml`:
```yaml
services:
  mcp-ga-server:
    # ... other config
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## Production Deployment

### Security Considerations

1. **Use HTTPS**: Deploy behind a reverse proxy (nginx, Caddy)
2. **Secure Credentials**: Use Docker secrets or external secret management
3. **Network Isolation**: Use custom networks and firewall rules
4. **Regular Updates**: Keep base image and dependencies updated

### Example nginx Configuration

```nginx
server {
    listen 443 ssl;
    server_name analytics-mcp.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Scaling

For high availability:

```yaml
services:
  mcp-ga-server:
    # ... other config
    deploy:
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### Monitoring

Add monitoring with Prometheus:

```yaml
services:
  mcp-ga-server:
    # ... other config
    labels:
      - "prometheus.scrape=true"
      - "prometheus.port=8000"
      - "prometheus.path=/metrics"
```

## Backup and Recovery

### Backup Configuration

```bash
# Backup .env file
cp .env .env.backup

# Export container config
docker inspect mcp-ga-server > container-config.json
```

### Recovery

```bash
# Restore from backup
cp .env.backup .env

# Rebuild and restart
make rebuild
```

## Logs

### View Logs

```bash
# Follow logs
make logs

# Last 100 lines
make logs-tail

# Export logs
docker-compose logs > server.log
```

### Log Rotation

Configure log rotation in `docker-compose.yml`:

```yaml
services:
  mcp-ga-server:
    # ... other config
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## Updates

### Update Server Code

```bash
# Pull latest changes
git pull

# Rebuild and restart
make rebuild
```

### Update Dependencies

Edit `Dockerfile` to update package versions, then:

```bash
make rebuild
```

## Support

For Docker-specific issues:
- Check [Docker documentation](https://docs.docker.com/)
- Review [Docker Compose documentation](https://docs.docker.com/compose/)
- Open an issue on GitHub
