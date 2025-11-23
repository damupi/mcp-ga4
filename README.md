# Google Analytics MCP Server

A Model Context Protocol (MCP) server that provides LLMs with programmatic access to Google Analytics 4 data and functionality. Built with [FastMCP](https://github.com/jlowin/fastmcp).

## Features

### 🛠️ Tools (9 Actions)

**Analytics Data API (v1beta)**
- `run_report` - Run analytics reports with dimensions, metrics, and advanced filters
- `run_realtime_report` - Get real-time analytics data (last 30 minutes)
- `list_dimensions` - Get available dimensions with descriptions
- `list_metrics` - Get available metrics with descriptions

**Analytics Admin API (v1beta)**
- `list_accounts` - List all GA4 accounts
- `list_properties` - List all GA4 properties for an account
- `get_property` - Get property details
- `list_data_streams` - List data streams for a property
- `get_data_stream` - Get data stream details

### 📊 Resources (7 Data Sources)

- `ga://accounts` - List all accounts
- `ga://accounts/{account_id}/properties` - List properties for account
- `ga://config` - Server configuration and status
- `ga://accounts/{account_id}/properties/{property_id}/summary` - Recent analytics summary (28 days)
- `ga://accounts/{account_id}/properties/{property_id}/top-pages` - Top 10 pages (7 days)
- `ga://accounts/{account_id}/properties/{property_id}/top-sources` - Top 10 traffic sources (7 days)
- `ga://accounts/{account_id}/properties/{property_id}/realtime` - Real-time data

### 💬 Prompts (4 Templates)

- `analyze_traffic` - Generate traffic analysis prompt
- `conversion_analysis` - Generate conversion funnel analysis prompt
- `audience_insights` - Generate audience demographics and behavior prompt
- `compare_periods` - Generate period-over-period comparison prompt

## Installation

### Prerequisites

- Python 3.10 or higher
- Google Cloud Project with Analytics APIs enabled
- OAuth 2.0 credentials from Google Cloud Console

### Install Dependencies

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-ga.git
cd mcp-ga

# Install with uv (recommended)
uv pip install fastmcp[google] google-api-python-client google-auth
```

## Authentication Setup

This server uses [FastMCP's built-in Google OAuth integration](https://fastmcp.wiki/en/integrations/google).

### Step 1: Enable Google Analytics APIs

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/library)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **Google Analytics Data API**
   - **Google Analytics Admin API**

### Step 2: Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **Create Credentials** → **OAuth 2.0 Client ID**
3. Configure OAuth consent screen if prompted
4. Choose **Web application** as application type
5. Add Authorized Javascript origins: `http://localhost`
6. Add authorized redirect URI: `http://localhost:8000/auth/callback`
7. Save your **Client ID** and **Client Secret**

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```bash
FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES=openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/analytics.readonly
```

## Usage

### Running the Server

**Development Mode (STDIO)**
```bash
fastmcp dev src/mcp_ga/server.py
```

**Production Mode (HTTP Transport)**
```bash
# Run with HTTP transport for remote access
fastmcp run src/mcp_ga/server.py --transport http

# Specify custom host and port
fastmcp run src/mcp_ga/server.py --transport http --host 0.0.0.0 --port 8080
```

The server will start on `http://localhost:8000` by default (HTTP mode).

### Running with Docker

**Quick Start:**
```bash
# Build the Docker image
make build

# Start the server
make up

# View logs
make logs

# Stop the server
make down
```

**Available Make Commands:**
- `make build` - Build the Docker image
- `make up` - Start the MCP server in background
- `make down` - Stop the MCP server
- `make restart` - Restart the server
- `make logs` - View server logs (follow mode)
- `make logs-tail` - View last 100 lines of logs
- `make status` - Check server status
- `make clean` - Remove all Docker resources
- `make shell` - Open a shell in the running container
- `make rebuild` - Rebuild and restart
- `make dev` - Run with live logs
- `make test` - Test server health endpoint

**Docker Configuration:**

The server runs in a Docker container with:
- Python 3.12 slim base image
- UV for fast dependency management
- HTTP transport on port 8000
- Automatic restart on failure
- Health checks every 30 seconds

Make sure your `.env` file is configured before running `make up`.

### Authentication Flow

1. Start the server
2. Connect with an MCP client (e.g., Claude Desktop)
3. You'll be redirected to Google OAuth login
4. Grant permissions to access Analytics data
5. You'll be redirected back and authenticated

### Using with Claude Desktop

**Option 1: STDIO Transport (Local)**

Add to your Claude Desktop configuration (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "ga-mcp-server": {
      "command": "fastmcp",
      "args": ["run", "src/mcp_ga/server.py"],
      "env": {
        "FASTMCP_SERVER_AUTH": "fastmcp.server.auth.providers.google.GoogleProvider",
        "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID": "your-client-id.apps.googleusercontent.com",
        "FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET": "GOCSPX-your-client-secret",
        "FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES": "openid,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/analytics.readonly"
      }
    }
  }
}
```

**Option 2: HTTP Transport (Remote)**

First, start the server with HTTP transport:
```bash
fastmcp run src/mcp_ga/server.py --transport http
```

Then configure Claude Desktop to connect via HTTP:
```json
{
  "mcpServers": {
    "ga-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote@latest",
        "http://localhost:8000/mcp"
      ]  
    }
  }
} 
```

### Debugging with MCP Inspector

You can use the [MCP Inspector](https://github.com/modelcontextprotocol/inspector) to test and debug the server.

**For Local Development:**
```bash
npx @modelcontextprotocol/inspector fastmcp dev src/mcp_ga/server.py
```

**For Docker/Remote Server:**
```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

## Example Usage

### List Accounts and Properties

```python
# Ask Claude:
"List my Google Analytics accounts"

# Claude will use:
list_accounts()

# Then ask:
"Show me properties for account 123456"

# Claude will use:
list_properties(account_id="123456")
```

### Run Analytics Report

```python
# Ask Claude:
"Show me the top 10 pages for property 987654321 
from 2024-01-01 to 2024-01-31"

# Claude will use:
run_report(
    property_id="987654321",
    start_date="2024-01-01",
    end_date="2024-01-31",
    dimensions=["pagePath"],
    metrics=["sessions", "screenPageViews"],
    limit=10
)
```

### Run Report with Filters

```python
# Ask Claude:
"Show me sessions from the US for property 987654321 in January"

# Claude will use:
run_report(
    property_id="987654321",
    start_date="2024-01-01",
    end_date="2024-01-31",
    dimensions=["country"],
    metrics=["sessions"],
    dimension_filter={
        "filter": {
            "fieldName": "country",
            "stringFilter": {
                "matchType": "EXACT",
                "value": "United States"
            }
        }
    }
)
```

### Get Analytics Summary

```python
# Ask Claude:
"What's the recent performance for account 123456 property 987654321?"

# Claude will access the resource:
ga://accounts/123456/properties/987654321/summary
```

### Traffic Analysis

```python
# Ask Claude:
"Analyze the traffic for property 987654321 over the last 30 days"

# Claude will use the prompt:
analyze_traffic(
    property_id="987654321",
    time_period="last 30 days"
)
```

## Available Dimensions and Metrics

### Common Dimensions
- `date` - Date of the session
- `country` - User's country
- `city` - User's city
- `deviceCategory` - Device type (desktop, mobile, tablet)
- `browser` - Browser name
- `operatingSystem` - Operating system
- `pagePath` - Page path
- `pageTitle` - Page title
- `sessionSource` - Traffic source
- `sessionMedium` - Traffic medium
- `sessionCampaignName` - Campaign name

### Common Metrics
- `activeUsers` - Number of active users
- `sessions` - Number of sessions
- `screenPageViews` - Number of page views
- `bounceRate` - Bounce rate
- `averageSessionDuration` - Average session duration
- `conversions` - Number of conversions
- `eventCount` - Number of events

For a complete list, use the `list_dimensions` and `list_metrics` tools.

## API Scopes

The server requires these OAuth scopes:

- `openid` - User identification
- `https://www.googleapis.com/auth/userinfo.email` - User email
- `https://www.googleapis.com/auth/analytics.readonly` - Read-only Analytics access

## Development

### Project Structure

```
mcp-ga/
├── src/mcp_ga/
│   ├── __init__.py       # Package initialization
│   ├── server.py         # Main FastMCP server
│   ├── auth.py           # Google OAuth authentication
│   ├── tools.py          # MCP tools (9 actions)
│   ├── resources.py      # MCP resources (7 data sources)
│   ├── prompts.py        # MCP prompts (4 templates)
│   └── utils.py          # Utility functions
├── examples/             # Usage examples
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── .dockerignore         # Docker ignore rules
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
├── Makefile              # Common commands
├── README.md             # This file
└── LICENSE               # MIT License
```

## Troubleshooting

### Authentication Errors

**Problem**: "Authentication failed" or "401 Unauthorized"

**Solution**: 
- Verify your OAuth credentials are correct
- Check that the redirect URI matches exactly: `http://localhost:8000/auth/callback`
- Ensure the Analytics Data API and Admin API are enabled in your Google Cloud project

### Permission Denied (403)

**Problem**: "Permission denied" when accessing a property

**Solution**:
- Verify you have access to the property in Google Analytics
- Check that you're using the correct property ID
- Ensure your OAuth token has the required scopes

### Rate Limiting (429)

**Problem**: "Rate limit exceeded"

**Solution**:
- Google Analytics API has usage limits
- Reduce the frequency of requests
- Implement exponential backoff in your client

### Account/Property ID Encoding

When using resources with account/property IDs, the IDs must be URL-encoded:

```
# Correct
ga://accounts/123456/properties/987654321/summary

# The server handles encoding/decoding automatically
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Resources

- [FastMCP Documentation](https://fastmcp.wiki)
- [Google Analytics Data API](https://developers.google.com/analytics/devguides/reporting/data/v1)
- [Google Analytics Admin API](https://developers.google.com/analytics/devguides/config/admin/v1)
- [Model Context Protocol](https://modelcontextprotocol.io)

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [FastMCP Discord](https://discord.gg/fastmcp)
- Review [Google Analytics API docs](https://developers.google.com/analytics)
