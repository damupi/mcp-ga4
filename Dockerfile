FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS uv

# Set working directory
WORKDIR /app

ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

COPY uv.lock pyproject.toml /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev --no-editable

# Copy project files
COPY pyproject.toml uv.lock /app/
# Copy README.md
COPY README.md ./README.md
# Copy src
COPY src /app/src
# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-editable

# Use Python 3.12 slim bookworm
FROM python:3.12-slim-bookworm

# Set working directory
WORKDIR /app

# Copy the virtual environment from the uv image
COPY --from=uv --chown=app:app /app/.venv /app/.venv

# Copy uv binary from the first stage
COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv

# Copy project files needed for installation
COPY --from=uv /app/pyproject.toml /app/
COPY --from=uv /app/src /app/src

# Ensure executables in the venv take precedence over system executables
ENV PATH="/app/.venv/bin:$PATH"

# Install the package
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e .

# Run the server
ENTRYPOINT ["mcp-ga4"]