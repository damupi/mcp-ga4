FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv for faster dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies from pyproject.toml
RUN uv pip install --system --no-cache \
    fastapi>=0.115.12 \
    fastmcp>=2.3.3 \
    google-api-python-client>=2.168.0 \
    google-auth-httplib2>=0.2.0 \
    google-auth-oauthlib>=1.2.2 \
    httpx>=0.28.1 \
    "mcp[cli]>=1.6.0" \
    sse-starlette>=2.3.3 \
    uvicorn>=0.34.2 \
    pyjwt>=2.10.1

# Copy application code
COPY . .

# Create placeholder client_secrets.json for lazy loading capability
RUN echo '{"installed":{"client_id":"placeholder","client_secret":"placeholder","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","redirect_uris":["http://localhost:8000/oauth2callback"]}}' > /app/client_secrets.json

# Debug: Check PORT environment variable first
RUN echo "=== Debug: Environment Variables ===" && \
    echo "PORT=${PORT:-8000}" && \
    echo "WORKSPACE_MCP_PORT=${WORKSPACE_MCP_PORT:-8000}" && \
    echo "WORKSPACE_MCP_BASE_URI=${WORKSPACE_MCP_BASE_URI:-http://localhost}"

# Debug: List files to verify structure
RUN echo "=== Debug: Listing app directory contents ===" && \
    ls -la /app && \
    echo "=== Debug: Checking if main.py exists ===" && \
    ls -la /app/main.py && \
    echo "=== Debug: Checking Python path and imports ===" && \
    python -c "import sys; print('Python path:', sys.path)" && \
    python -c "import core.server; print('Server import successful')" && \
    echo "=== Debug: Testing health endpoint ===" && \
    python -c "from core.server import health_check; print('Health check function exists')"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expose port (use default of 8000 if PORT not set)
EXPOSE 8000
# Expose additional port if PORT environment variable is set to a different value
ARG PORT
EXPOSE ${PORT:-8000}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD sh -c 'curl -f http://localhost:${PORT:-8000}/health || exit 1'

# Debug startup
RUN echo "=== Debug: Final startup test ===" && \
    python -c "print('Testing main.py import...'); import main; print('Main.py import successful')"

# Command to run the application
CMD ["python", "main.py", "--transport", "streamable-http"]