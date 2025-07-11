# server.py
import asyncio
import threading
import uvicorn
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.logging import configure_logging, get_logger
from mcp_ga4 import resources, tools, prompts
from mcp_ga4.auth import (
    create_oauth_flow, 
    create_oauth_flow_for_callback,
    get_client_id_from_request, 
    save_credentials, 
    is_authenticated,
    get_redirect_uri,
    validate_scopes_for_ga4
)
from dotenv import load_dotenv
import os
import traceback
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

# Configure logging using MCP utilities
configure_logging(
    level=os.getenv("MCP_LOG_LEVEL", "DEBUG")
)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(title="MCP GA4 Server", description="OAuth-enabled MCP server for Google Analytics 4")

# OAuth routes
@app.get("/")
async def root():
    """Root endpoint to check authentication status"""
    try:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            return {"status": "error", "message": "GOOGLE_CLIENT_ID not configured"}
        
        client_id = client_id.strip('"\'')
        if is_authenticated(client_id):
            return {"status": "authenticated", "message": "User is authenticated with Google Analytics"}
        else:
            return {"status": "not_authenticated", "message": "Please visit /authorize to authenticate"}
    except Exception as e:
        return {"status": "error", "message": f"Authentication check failed: {str(e)}"}

@app.get("/authorize")
async def authorize(request: Request):
    """Start OAuth authorization flow"""
    try:
        client_id = get_client_id_from_request(request)
        flow = create_oauth_flow(client_id)
        
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true'
        )
        
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        logger.error(f"Authorization error: {e}")
        raise HTTPException(status_code=500, detail=f"Authorization failed: {str(e)}")

@app.get("/oauth2callback")
async def oauth2callback(request: Request, code: str = Query(...), state: str = Query(None)):
    """Handle OAuth callback with flexible scope validation"""
    try:
        client_id = get_client_id_from_request(request)
        
        # Manual token exchange to handle scope flexibility
        import requests
        
        # Get client configuration
        client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
        if not client_secret:
            raise ValueError("GOOGLE_CLIENT_SECRET environment variable not set")
        
        client_secret = client_secret.strip('"\'')
        client_id = client_id.strip('"\'')
        
        # Exchange authorization code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': get_redirect_uri(),
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=token_data)
        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.text}")
        
        token_info = response.json()
        
        # Get the scopes that were actually granted
        granted_scopes_str = token_info.get('scope', '')
        granted_scopes = granted_scopes_str.split() if granted_scopes_str else []
        
        # Validate that we have sufficient scopes for GA4
        if not validate_scopes_for_ga4(granted_scopes):
            logger.error(f"Insufficient scopes for GA4. Granted: {granted_scopes}")
            raise Exception("Authentication successful but insufficient permissions for Google Analytics. Please ensure you have access to Google Analytics.")
        
        # Create credentials with the granted scopes
        from google.oauth2.credentials import Credentials
        credentials = Credentials(
            token=token_info['access_token'],
            refresh_token=token_info.get('refresh_token'),
            token_uri=token_url,
            client_id=client_id,
            client_secret=client_secret,
            scopes=granted_scopes
        )
        
        # Save credentials
        save_credentials(client_id, credentials)
        
        # Return a user-friendly HTML page instead of JSON
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Authentication Successful - MCP GA4</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                }}
                .success-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                    color: #4CAF50;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .message {{
                    color: #666;
                    font-size: 16px;
                    line-height: 1.5;
                    margin-bottom: 30px;
                }}
                .success-details {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    text-align: left;
                }}
                .detail-item {{
                    margin-bottom: 10px;
                    font-size: 14px;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #333;
                }}
                .detail-value {{
                    color: #666;
                }}
                .scope-list {{
                    max-height: 100px;
                    overflow-y: auto;
                    font-size: 12px;
                    background: white;
                    border-radius: 4px;
                    padding: 10px;
                    margin-top: 5px;
                }}
                .scope-item {{
                    padding: 2px 0;
                    border-bottom: 1px solid #eee;
                }}
                .scope-item:last-child {{
                    border-bottom: none;
                }}
                .close-button {{
                    background: #667eea;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background 0.3s;
                }}
                .close-button:hover {{
                    background: #5a67d8;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>Authentication Successful!</h1>
                <p class="message">
                    You have successfully authenticated with Google Analytics. 
                    Your MCP GA4 server is now ready to use.
                </p>
                
                <div class="success-details">
                    <div class="detail-item">
                        <span class="detail-label">Status:</span>
                        <span class="detail-value">✅ Ready for GA4 operations</span>
                    </div>
                    <div class="detail-item">
                        <span class="detail-label">Scopes Granted:</span>
                        <div class="scope-list">
                            {chr(10).join(f'<div class="scope-item">{scope}</div>' for scope in granted_scopes)}
                        </div>
                    </div>
                </div>
                
                <p class="message">
                    You can now close this page and return to your MCP client.
                </p>
                
                <button class="close-button" onclick="window.close()">Close This Page</button>
            </div>
            
            <script>
                // Auto-close after 10 seconds as fallback
                setTimeout(() => {{
                    window.close();
                }}, 10000);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        # Return an error HTML page instead of HTTPException
        error_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Authentication Failed - MCP GA4</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                    margin: 0;
                    padding: 0;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    padding: 40px;
                    border-radius: 16px;
                    box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 90%;
                }}
                .error-icon {{
                    font-size: 64px;
                    margin-bottom: 20px;
                    color: #e74c3c;
                }}
                h1 {{
                    color: #333;
                    margin-bottom: 20px;
                    font-size: 28px;
                    font-weight: 600;
                }}
                .message {{
                    color: #666;
                    font-size: 16px;
                    line-height: 1.5;
                    margin-bottom: 30px;
                }}
                .error-details {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 8px;
                    margin-bottom: 30px;
                    text-align: left;
                    font-size: 14px;
                    color: #666;
                }}
                .close-button {{
                    background: #e74c3c;
                    color: white;
                    border: none;
                    padding: 12px 30px;
                    border-radius: 8px;
                    font-size: 16px;
                    cursor: pointer;
                    transition: background 0.3s;
                }}
                .close-button:hover {{
                    background: #c0392b;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error-icon">❌</div>
                <h1>Authentication Failed</h1>
                <p class="message">
                    We encountered an error while trying to authenticate with Google Analytics.
                </p>
                
                <div class="error-details">
                    <strong>Error:</strong> {str(e)}
                </div>
                
                <p class="message">
                    Please try the authentication process again or contact support if the issue persists.
                </p>
                
                <button class="close-button" onclick="window.close()">Close This Page</button>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=error_html, status_code=500)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

# MCP Server lifecycle management
mcp_server = None
mcp_thread = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP server lifecycle"""
    global mcp_server, mcp_thread
    
    # Start MCP server in a separate thread
    def run_mcp_server():
        global mcp_server
        try:
            # Create MCP server instance
            mcp_server = FastMCP("MCP GA4")
            
            # Register resources
            @mcp_server.resource("ga4://properties")
            def list_properties():
                return resources.list_ga4_properties()
            
            @mcp_server.resource("ga4://properties/{property_id}")
            def get_property_details(property_id: str):
                return resources.get_ga4_property_details(property_id)
            
            @mcp_server.resource("ga4://properties/{property_id}/metadata")
            def get_metadata(property_id: str):
                return resources.get_ga4_metadata(property_id)
            
            # Register prompts
            @mcp_server.prompt("ga4-report-prompt")
            def ga4_report_prompt():
                return prompts.ga4_report_prompt()
            
            @mcp_server.prompt("ga4-property-prompt")
            def ga4_property_prompt():
                return prompts.ga4_property_prompt()
            
            # Register tools
            @mcp_server.tool("list_ga4_properties")
            def list_properties_tool():
                return tools.list_ga4_properties()
            
            @mcp_server.tool("get_metadata")
            def get_metadata_tool(property_id: str):
                return tools.get_metadata(property_id)
            
            @mcp_server.tool("run_report")
            def run_report_tool(property_id: str, start_date: str, end_date: str, metrics: list, dimensions: list = None):
                return tools.run_report(property_id, start_date, end_date, metrics, dimensions)
            
            @mcp_server.tool("batch_run_reports")
            def batch_run_reports_tool(property_id: str, requests: list):
                return tools.batch_run_reports(property_id, requests)
            
            @mcp_server.tool("run_pivot_report")
            def run_pivot_report_tool(property_id: str, start_date: str, end_date: str, metrics: list, dimensions: list, pivots: list):
                return tools.run_pivot_report(property_id, start_date, end_date, metrics, dimensions, pivots)
            
            @mcp_server.tool("batch_run_pivot_reports")
            def batch_run_pivot_reports_tool(property_id: str, requests: list):
                return tools.batch_run_pivot_reports(property_id, requests)
            
            @mcp_server.tool("check_compatibility")
            def check_compatibility_tool(property_id: str, dimensions: list = None, metrics: list = None):
                return tools.check_compatibility(property_id, dimensions, metrics)
            
            # Run MCP server on stdin/stdout
            mcp_server.run()
            
        except Exception as e:
            logger.error(f"MCP server error: {e}")
            logger.error(traceback.format_exc())
    
    # Start MCP server thread
    mcp_thread = threading.Thread(target=run_mcp_server, daemon=True)
    mcp_thread.start()
    
    logger.info("MCP server started in background thread")
    
    yield
    
    # Cleanup on shutdown
    if mcp_server:
        logger.info("Shutting down MCP server")

# Apply lifespan to FastAPI app
app.router.lifespan_context = lifespan

def run_server():
    """Run the FastAPI server"""
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    
    logger.info(f"Starting MCP GA4 server on {host}:{port}")
    logger.info(f"OAuth redirect URI: {get_redirect_uri()}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()