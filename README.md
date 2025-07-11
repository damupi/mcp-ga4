# MCP GA4 Server

An MCP (Model Context Protocol) server for Google Analytics 4 (GA4), enabling LLMs and clients to interact with GA4 data via the MCP standard. This project is designed for use with [Claude Desktop](https://github.com/Bartender-bit/Remote-MCP-Server-for-Claude-Desktop), [Cursor](https://www.cursor.so/), and other MCP-compatible clients.

## Table of Contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Authentication Setup](#authentication-setup)
- [Running the Server](#running-the-server)
- [Configuration](#configuration)
- [Integration Examples](#integration-examples)
- [Contributing](#contributing)
- [License](#license)
- [References](#references)

---

## Features

- Exposes GA4 data and reporting via the Model Context Protocol (MCP)
- **OAuth 2.0 authentication** for secure user-based access
- Multiple GA4 report types: standard reports, pivot reports, and batch reports
- Web-based authentication flow
- Ready for integration with Claude Desktop and Cursor

## Requirements

- Python 3.12+ (or Docker)
- [uv](https://www.pythonuv.com/) (for local development)
- Google Cloud project with GA4 Data API and GA4 Admin API enabled
- OAuth 2.0 credentials configured in Google Cloud Console

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/mcp-ga4.git
   cd mcp-ga4
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```

## Authentication Setup

This server now uses **OAuth 2.0** instead of service account authentication. For detailed setup instructions, see [SETUP.md](SETUP.md).

### Quick Setup Summary:

1. **Set up Google Cloud Console:**
   - Create a project and enable GA4 APIs
   - Configure OAuth consent screen
   - Create OAuth 2.0 credentials

2. **Create `.env` file:**
   ```env
   GOOGLE_CLIENT_ID=your_client_id_here
   GOOGLE_CLIENT_SECRET=your_client_secret_here
   MCP_TRANSPORT=streamable-http
   MCP_HOST=127.0.0.1
   MCP_PORT=8000
   ```

3. **Authenticate:**
   - Start the server
   - Visit `http://localhost:8000/authorize`
   - Complete the OAuth flow

## Running the Server

### Web Server Mode (Recommended)

For OAuth authentication, run the server in web mode:

```bash
# Set environment variables
export MCP_TRANSPORT=streamable-http
export MCP_PORT=8000

# Start the server
python -m mcp_ga4.server
```

The server will start on `http://localhost:8000`

### StdIO Mode (Traditional MCP)

For traditional MCP stdio communication:

```bash
# Default transport is stdio
python -m mcp_ga4.server
```

### Development Mode

To test and debug with the MCP inspector:

```bash
mcp dev src/mcp_ga4/server.py
```

### With Docker

#### Build and run with Docker Compose

1. **Build and start the container:**
   ```bash
   docker-compose up --build
   ```

2. **Environment variables** can be set in the `docker-compose.yml` or via `.env`.

#### Standalone Docker

```bash
docker build -t mcp-ga4 .
docker run -it --rm \
  -p 8000:8000 \
  -e GOOGLE_CLIENT_ID=your_client_id \
  -e GOOGLE_CLIENT_SECRET=your_client_secret \
  -e MCP_TRANSPORT=streamable-http \
  mcp-ga4
```

## Configuration

### OAuth 2.0 Setup

**Google Cloud Console Setup:**

1. **Create OAuth 2.0 credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "APIs & Services" > "Credentials"
   - Create OAuth client ID (Web application)
   - Add redirect URI: `http://localhost:8000/oauth2callback`

2. **Enable required APIs:**
   - Google Analytics Data API
   - Google Analytics Admin API

3. **Configure OAuth consent screen:**
   - Add your email as a test user
   - Configure required fields

### Environment Variables

| Variable                | Description                                 | Example Value           |
|-------------------------|---------------------------------------------|------------------------|
| `GOOGLE_CLIENT_ID`      | OAuth 2.0 client ID                        | `123456789.apps.googleusercontent.com` |
| `GOOGLE_CLIENT_SECRET`  | OAuth 2.0 client secret                    | `GOCSPX-abc123...`     |
| `MCP_TRANSPORT`         | Transport mode (`stdio` or `streamable-http`) | `streamable-http`      |
| `MCP_HOST`              | Server host                                 | `0.0.0.0`              |
| `MCP_PORT`              | Server port                                 | `8000`                 |
| `MCP_LOG_LEVEL`         | Logging level (`DEBUG`, `INFO`, etc.)       | `DEBUG`                |

## Integration Examples

### Cursor

To use the server with Cursor, add the following to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "mcp-ga4": {
      "command": "python",
      "args": [
        "-m",
        "mcp_ga4.server"
      ],
      "env": {
        "GOOGLE_CLIENT_ID": "your_client_id_here",
        "GOOGLE_CLIENT_SECRET": "your_client_secret_here",
        "MCP_TRANSPORT": "streamable-http",
        "MCP_HOST": "localhost",
        "MCP_PORT": "8000",
        "MCP_LOG_LEVEL": "DEBUG"
      },
      "cwd": "${workspaceFolder}/mcp-ga4"
    }
  }
}
```

### Claude Desktop

1. Open your Claude Desktop config at:
   ```
   ~/Library/Application Support/Claude/claude_desktop_config.json
   ```
2. Add your MCP server under `mcpServers`:

```json
{
  "mcpServers": {
    "mcp-ga4": {
      "command": "python",
      "args": [
        "-m",
        "mcp_ga4.server"
      ],
      "env": {
        "GOOGLE_CLIENT_ID": "your_client_id_here",
        "GOOGLE_CLIENT_SECRET": "your_client_secret_here",
        "MCP_TRANSPORT": "streamable-http",
        "MCP_HOST": "localhost",
        "MCP_PORT": "8000",
        "MCP_LOG_LEVEL": "DEBUG"
      },
      "cwd": "/absolute/path/to/mcp-ga4"
    }
  }
}
```

3. Save and restart Claude Desktop.

#### Claude Desktop (Windows)

For Windows users:

1. Open your Claude Desktop config at:
   ```
   %APPDATA%\Claude\claude_desktop_config.json
   ```
2. Add your MCP server configuration:

```json
{
  "mcpServers": {
    "mcp-ga4": {
      "command": "python",
      "args": [
        "-m",
        "mcp_ga4.server"
      ],
      "env": {
        "GOOGLE_CLIENT_ID": "your_client_id_here",
        "GOOGLE_CLIENT_SECRET": "your_client_secret_here",
        "MCP_TRANSPORT": "streamable-http",
        "MCP_HOST": "localhost",
        "MCP_PORT": "8000",
        "MCP_LOG_LEVEL": "DEBUG"
      },
      "cwd": "C:/path/to/mcp-ga4"
    }
  }
}
```

3. Save and restart Claude Desktop.

## Available Tools

Once authenticated, you can use these MCP tools:

- **`list_ga4_properties`**: List all accessible GA4 properties
- **`run_report`**: Generate standard GA4 reports
- **`run_pivot_report`**: Generate pivot reports
- **`batch_run_reports`**: Run multiple reports in batch
- **`check_compatibility`**: Check dimension/metric compatibility

## Authentication Flow

1. Start the server in web mode
2. Visit `http://localhost:8000/authorize` to begin OAuth flow
3. Complete Google authentication
4. Server stores credentials automatically
5. Use MCP tools with authenticated access

## Migration from Service Account

If you're migrating from service account authentication:

1. Remove `google-credentials.json` file
2. Remove `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Follow the OAuth 2.0 setup instructions in [SETUP.md](SETUP.md)
4. Re-authenticate using the web flow

## Troubleshooting

See [SETUP.md](SETUP.md) for detailed troubleshooting information.

Common issues:
- **Authentication required**: Visit `/authorize` to authenticate
- **Invalid redirect URI**: Ensure redirect URI is configured in Google Cloud Console
- **No client ID found**: Check environment variables

## Contributing

Pull requests are welcome! Please open an issue to discuss major changes.

## License

[MIT](LICENSE)

## References

- [Model Context Protocol (MCP) Introduction](https://modelcontextprotocol.io/introduction)
- [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [OAuth 2.0 for Web Server Applications](https://developers.google.com/identity/protocols/oauth2/web-server)
- [Claude Desktop Remote MCP Server](https://github.com/Bartender-bit/Remote-MCP-Server-for-Claude-Desktop)

---

Feel free to further customize the README for your organization or add more usage examples as your project evolves.