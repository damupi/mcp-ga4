# MCP GA4 OAuth 2.0 Setup Guide

This guide will help you set up OAuth 2.0 authentication for the MCP GA4 server.

## Prerequisites

1. **Google Cloud Console Project**: You need a Google Cloud project with the Analytics API enabled
2. **Google Analytics 4 Property**: Access to at least one GA4 property
3. **Python 3.12+**: The server requires Python 3.12 or higher

## Step 1: Set up Google Cloud Console

### 1.1 Create or Select a Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

### 1.2 Enable Required APIs

1. In the Cloud Console, go to **APIs & Services** > **Library**
2. Search for and enable the following APIs:
   - **Google Analytics Admin API**
   - **Google Analytics Data API**

### 1.3 Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type (unless you have a Google Workspace account)
3. Fill in the required information:
   - App name: "MCP GA4 Server"
   - User support email: Your email
   - Developer contact information: Your email
4. Click **Save and Continue**
5. In the **Scopes** section, you can skip adding scopes for now
6. Add test users (your email address) in the **Test users** section
7. Click **Save and Continue**

### 1.4 Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Select **Web application** as the application type
4. Set the name to "MCP GA4 OAuth Client"
5. Add authorized redirect URIs based on your deployment:
   - **For localhost**: `http://localhost:8000/oauth2callback`
   - **For production**: `https://yourdomain.com/oauth2callback`
6. Click **Create**
7. Download the credentials JSON file and save it securely

## Step 2: Set up Environment Variables

Create a `.env` file in your project root with the following variables:

```env
# OAuth 2.0 Configuration
GOOGLE_CLIENT_ID="your_client_id_here"
GOOGLE_CLIENT_SECRET="your_client_secret_here"

# Server Configuration
MCP_HOST="0.0.0.0"
MCP_PORT="8000"
MCP_TRANSPORT="streamable-http"
MCP_LOG_LEVEL="DEBUG"

# Optional: Custom redirect URI (for production deployments)
OAUTH_REDIRECT_URI="https://yourdomain.com/oauth2callback"

# Optional: Default project ID
GOOGLE_PROJECT_ID="your_project_id_here"
```

**Notes**: 
- Double quotes around values are fine and recommended
- Replace `your_client_id_here` and `your_client_secret_here` with values from your credentials JSON
- For production deployments, set `OAUTH_REDIRECT_URI` to match your domain

## Step 3: Install Dependencies

Using `uv` (recommended):

```bash
uv sync
```

Or using pip:

```bash
pip install -e .
```

## Step 4: Start the Server

### Option A: Web Server Mode (Recommended for OAuth)

```bash
# Set transport to HTTP mode
export MCP_TRANSPORT=streamable-http

# Start the server
python -m mcp_ga4.server
```

The server will start on `http://localhost:8000`

### Option B: StdIO Mode (Traditional MCP)

```bash
# Leave MCP_TRANSPORT as default or set to stdio
python -m mcp_ga4.server
```

## Step 5: Authenticate with Google

### 5.1 Visit the Authorization URL

1. Open your browser and go to `http://localhost:8000/authorize` (or your production domain)
2. You'll be redirected to Google's OAuth consent screen
3. Log in with your Google account that has access to GA4 properties
4. Grant the requested permissions
5. You'll be redirected back to the server with a success message

### 5.2 Verify Authentication

Visit `http://localhost:8000/auth-status` to check your authentication status.

## Step 6: Configure Your MCP Client

### For Claude Desktop

Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mcp-ga4": {
      "command": "python",
      "args": ["-m", "mcp_ga4.server"],
      "env": {
        "GOOGLE_CLIENT_ID": "your_client_id_here",
        "GOOGLE_CLIENT_SECRET": "your_client_secret_here",
        "MCP_TRANSPORT": "streamable-http",
        "MCP_HOST": "localhost",
        "MCP_PORT": "8000"
      }
    }
  }
}
```

### For Other MCP Clients

Configure your client to connect to `http://localhost:8000/mcp` with the appropriate headers.

## Production Deployment

### Cloudflare Workers

For Cloudflare Workers deployment:

1. **Set environment variables**:
   ```env
   MCP_HOST="your-worker-domain.workers.dev"
   OAUTH_REDIRECT_URI="https://your-worker-domain.workers.dev/oauth2callback"
   ```

2. **Add redirect URI to Google Cloud Console**:
   - `https://your-worker-domain.workers.dev/oauth2callback`

### Google Cloud Run

For Google Cloud Run deployment:

1. **Set environment variables**:
   ```env
   MCP_HOST="your-service-name.a.run.app"
   OAUTH_REDIRECT_URI="https://your-service-name.a.run.app/oauth2callback"
   ```

2. **Add redirect URI to Google Cloud Console**:
   - `https://your-service-name.a.run.app/oauth2callback`

### Other Production Environments

1. **Set your domain**:
   ```env
   MCP_HOST="yourdomain.com"
   OAUTH_REDIRECT_URI="https://yourdomain.com/oauth2callback"
   ```

2. **Update Google Cloud Console**:
   - Add your production redirect URI
   - Add your domain to authorized domains

## Troubleshooting

### Common Issues

1. **"No client ID found"**: Make sure `GOOGLE_CLIENT_ID` is set in your environment variables
2. **"Authentication required"**: Visit `/authorize` to authenticate with Google
3. **"Invalid redirect URI"**: Ensure the redirect URI matches what's configured in Google Cloud Console
4. **"Access denied"**: Make sure your Google account has access to GA4 properties
5. **"Quoted values"**: Double quotes in .env files are fine and handled automatically

### Debug Mode

Set `MCP_LOG_LEVEL=DEBUG` in your environment to see detailed logging information.

### Testing the Setup

1. Visit `http://localhost:8000` (or your domain) to see the server info
2. Visit `http://localhost:8000/auth-status` to check authentication
3. Use the MCP tools to test GA4 access

### Environment Variables with Quotes

It's perfectly fine to use double quotes around your environment variables in the `.env` file:

```env
GOOGLE_CLIENT_ID="123456789-abcdef.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="GOCSPX-your_secret_here"
```

The code automatically strips quotes from values.

## Available MCP Tools

Once authenticated, you can use these tools:

- `list_ga4_properties`: List all accessible GA4 properties
- `run_report`: Generate GA4 reports
- `run_pivot_report`: Generate pivot reports
- `batch_run_reports`: Run multiple reports in batch
- `check_compatibility`: Check dimension/metric compatibility

## Security Notes

- Keep your OAuth credentials secure and never commit them to version control
- Token files (e.g., `token_your_client_id.json`) are created automatically and should also be kept secure
- The server runs on localhost by default for security
- Consider using environment variables or secure secret management for production deployments
- Use HTTPS in production environments

## Migration from Service Account

If you're migrating from service account authentication:

1. Remove the `google-credentials.json` file
2. Remove the `GOOGLE_APPLICATION_CREDENTIALS` environment variable
3. Follow the OAuth setup steps above
4. Re-authenticate using the web flow

The API calls and functionality remain the same - only the authentication method changes. 