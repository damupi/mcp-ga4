the .env file contains the variables:
- GOOGLE_PROJECT_ID
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET
- MCP_DEGUG
- MCP_LOG_LEVEL="DEBUG"
- MCP_TRANSPORT="streamable-http"
- MCP_PORT="8000"
- MCP_HOST="localhost"
- MCP_PATH="/mcp"

- I've created OAuth 2.0 credentials with the autorised redirect URI: "http://localhost:8000/oauth2callback"
- I've Configureconfigured consent screen
- I've enable GA4 APIs
- The MCP server of GA4 does API calls and it requires for that, this scope: https://www.googleapis.com/auth/analytics.readonly
- The MCP server has Google OAuth 2.0 authentication. Documentation: https://github.com/googleapis/google-api-python-client/blob/main/docs/README.md