# OAuth 2.0 authentication for Google Analytics 4
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from googleapiclient.discovery import build
from dotenv import load_dotenv
from fastapi import Request as FastAPIRequest
import logging

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

# OAuth 2.0 configuration - Only request what we need for GA4
# Google may add additional scopes automatically (userinfo.profile, userinfo.email, openid, etc.)
SCOPES = [
    'https://www.googleapis.com/auth/analytics.readonly'
]

# Scopes that Google commonly adds automatically - we'll accept these without error
GOOGLE_AUTOMATIC_SCOPES = [
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/webmasters.readonly',
    'https://www.googleapis.com/auth/analytics.manage.users',
    'openid'
]

def get_redirect_uri() -> str:
    """
    Get the redirect URI based on environment configuration.
    
    Returns:
        str: The redirect URI for OAuth flow
    """
    # Check if we have a custom redirect URI
    custom_redirect = os.getenv('OAUTH_REDIRECT_URI')
    if custom_redirect:
        return custom_redirect
    
    # Build redirect URI from host and port
    host = os.getenv('MCP_HOST', 'localhost')
    port = os.getenv('MCP_PORT', '8000')
    
    # Handle 0.0.0.0 case - Google doesn't allow 0.0.0.0 in redirect URIs
    if host == '0.0.0.0':
        host = 'localhost'
    
    # Use https for production domains, http for localhost
    if host in ['localhost', '127.0.0.1']:
        protocol = 'http'
        full_host = f"{host}:{port}"
    else:
        protocol = 'https'
        full_host = host  # Don't include port for production domains
    
    return f"{protocol}://{full_host}/oauth2callback"

def get_client_id_from_request(request: FastAPIRequest) -> str:
    """
    Extract client ID from the request headers or return default from environment.
    
    Args:
        request: FastAPI request object
        
    Returns:
        str: Client ID for OAuth flow
    """
    # Try to get client ID from headers first
    client_id = request.headers.get('X-Client-ID')
    if client_id:
        return client_id
    
    # Fallback to environment variable
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        raise ValueError("No client ID found in request headers or environment variables")
    
    return client_id

def create_oauth_flow(client_id: str = None) -> Flow:
    """
    Create OAuth 2.0 flow for Google Analytics authentication.
    
    Args:
        client_id: Optional client ID, will use environment variable if not provided
        
    Returns:
        Flow: Configured OAuth flow
    """
    if not client_id:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
    
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")
    
    # Remove quotes from client_id and client_secret if present
    client_id = client_id.strip('"\'')
    client_secret = client_secret.strip('"\'')
    
    # Get dynamic redirect URI
    redirect_uri = get_redirect_uri()
    
    # Create client configuration
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    
    # Set redirect URI
    flow.redirect_uri = redirect_uri
    
    return flow

def create_oauth_flow_for_callback(client_id: str = None) -> Flow:
    """
    Create OAuth 2.0 flow for handling the callback with flexible scope validation.
    
    Args:
        client_id: Optional client ID, will use environment variable if not provided
        
    Returns:
        Flow: Configured OAuth flow with flexible scope validation
    """
    if not client_id:
        client_id = os.getenv('GOOGLE_CLIENT_ID')
    
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in environment variables")
    
    # Remove quotes from client_id and client_secret if present
    client_id = client_id.strip('"\'')
    client_secret = client_secret.strip('"\'')
    
    # Get dynamic redirect URI
    redirect_uri = get_redirect_uri()
    
    # Create client configuration
    client_config = {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }
    
    # Create flow - we'll handle scope validation manually
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES
    )
    
    # Set redirect URI
    flow.redirect_uri = redirect_uri
    
    return flow

def validate_scopes_for_ga4(granted_scopes: list[str]) -> bool:
    """
    Validate that the granted scopes include at least analytics.readonly for GA4.
    
    Args:
        granted_scopes: List of scopes that were granted by Google
        
    Returns:
        bool: True if we have sufficient scopes for GA4, False otherwise
    """
    # We need at least analytics.readonly for basic GA4 functionality
    required_scope = 'https://www.googleapis.com/auth/analytics.readonly'
    
    # Check if we have the required scope
    has_required = required_scope in granted_scopes
    
    if not has_required:
        logger.warning(f"Required scope {required_scope} not found in granted scopes: {granted_scopes}")
    
    return has_required

def get_stored_credentials(client_id: str) -> Credentials:
    """
    Get stored OAuth credentials for a client.
    
    Args:
        client_id: Client ID to get credentials for
        
    Returns:
        Credentials: Valid OAuth credentials or None
    """
    # Clean client_id for filename
    clean_client_id = client_id.replace('/', '_').replace(':', '_')
    token_file = f"token_{clean_client_id}.json"
    
    if not os.path.exists(token_file):
        return None
    
    try:
        # Load credentials with flexible scope handling
        creds = Credentials.from_authorized_user_file(token_file)
        
        # Validate that we have sufficient scopes for GA4
        if creds.scopes and not validate_scopes_for_ga4(creds.scopes):
            logger.error(f"Stored credentials don't have sufficient scopes for GA4: {creds.scopes}")
            return None
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            save_credentials(client_id, creds)
        
        return creds
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        return None

def save_credentials(client_id: str, credentials: Credentials):
    """
    Save OAuth credentials to file.
    
    Args:
        client_id: Client ID to save credentials for
        credentials: Credentials object to save
    """
    # Clean client_id for filename
    clean_client_id = client_id.replace('/', '_').replace(':', '_')
    token_file = f"token_{clean_client_id}.json"
    
    try:
        with open(token_file, 'w') as f:
            f.write(credentials.to_json())
        logger.info(f"Credentials saved to {token_file}")
        
        # Log the scopes that were granted
        if credentials.scopes:
            logger.info(f"Granted scopes: {credentials.scopes}")
            
            # Check if we have GA4 scopes
            if validate_scopes_for_ga4(credentials.scopes):
                logger.info("✅ Sufficient scopes for GA4 functionality")
            else:
                logger.warning("⚠️ Missing required GA4 scopes")
        
    except Exception as e:
        logger.error(f"Error saving credentials: {e}")

def get_ga4_service(client_id: str, service_type: str = 'data'):
    """
    Create an authenticated Google Analytics 4 service using OAuth 2.0.
    
    Args:
        client_id: Client ID for OAuth authentication
        service_type: Type of service ('data' or 'admin')
        
    Returns:
        BetaAnalyticsDataClient or AnalyticsAdminServiceClient: Authenticated GA4 service
    """
    credentials = get_stored_credentials(client_id)
    
    if not credentials:
        raise ValueError(f"No valid credentials found for client {client_id}. Please authorize first.")
    
    try:
        if service_type == 'data':
            return BetaAnalyticsDataClient(credentials=credentials)
        elif service_type == 'admin':
            return AnalyticsAdminServiceClient(credentials=credentials)
        else:
            raise ValueError(f"Invalid service type: {service_type}")
    except Exception as e:
        logger.error(f"Error creating GA4 service: {e}")
        raise

def ga4_client(client_id: str = None, type: str = 'data'):
    """
    Create an authenticated Google Analytics 4 client using OAuth 2.0.
    
    Args:
        client_id: Client ID for OAuth authentication
        type: The type of client to create, either 'admin' or 'data'
        
    Returns:
        AnalyticsAdminServiceClient or BetaAnalyticsDataClient: An authenticated GA4 client
    """
    if not client_id:
        # Try to get from environment if not provided
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not client_id:
            raise ValueError("Client ID must be provided or set in GOOGLE_CLIENT_ID environment variable")
    
    # Remove quotes from client_id if present
    client_id = client_id.strip('"\'')
    
    return get_ga4_service(client_id, type)

def is_authenticated(client_id: str) -> bool:
    """
    Check if a client is authenticated with valid credentials.
    
    Args:
        client_id: Client ID to check
        
    Returns:
        bool: True if authenticated, False otherwise
    """
    try:
        credentials = get_stored_credentials(client_id)
        return credentials is not None and credentials.valid
    except Exception:
        return False
