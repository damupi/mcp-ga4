.PHONY: help build up down restart logs logs-tail status clean shell rebuild dev test

# Default target
help:
	@echo "Google Analytics MCP Server - Docker Commands"
	@echo ""
	@echo "Available commands:"
	@echo "  make build       - Build the Docker image"
	@echo "  make up          - Start the MCP server in background"
	@echo "  make down        - Stop the MCP server"
	@echo "  make restart     - Restart the server"
	@echo "  make logs        - View server logs (follow mode)"
	@echo "  make logs-tail   - View last 100 lines of logs"
	@echo "  make status      - Check server status"
	@echo "  make clean       - Remove all Docker resources"
	@echo "  make shell       - Open a shell in the running container"
	@echo "  make rebuild     - Rebuild and restart"
	@echo "  make dev         - Run with live logs"
	@echo "  make test        - Test server health endpoint"

# Build the Docker image
build:
	docker-compose build

# Start the server in background
up:
	docker-compose up -d
	@echo "Server started! Access at http://localhost:8000"
	@echo "Health check: http://localhost:8000/health"
	@echo "MCP endpoint: http://localhost:8000/mcp"

# Stop the server
down:
	docker-compose down

# Restart the server
restart: down up

# View logs (follow mode)
logs:
	docker-compose logs -f

# View last 100 lines of logs
logs-tail:
	docker-compose logs --tail=100

# Check server status
status:
	@docker-compose ps
	@echo ""
	@echo "Health check:"
	@curl -s http://localhost:8000/health | python -m json.tool || echo "Server not responding"

# Clean up all Docker resources
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Open a shell in the running container
shell:
	docker-compose exec mcp-ga-server /bin/bash

# Rebuild and restart
rebuild: clean build up

# Run with live logs
dev: up logs

# Test health endpoint
test:
	@echo "Testing health endpoint..."
	@curl -s http://localhost:8000/health | python -m json.tool
