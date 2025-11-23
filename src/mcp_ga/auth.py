"""Google Analytics MCP Server - Authentication Module

This module handles authentication with Google Analytics APIs using FastMCP's
Google OAuth integration: https://fastmcp.wiki/en/integrations/google
"""

from typing import Optional

from google.auth.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import google.auth.transport.requests


class AccessTokenCredentials(Credentials):
    """Credentials that only use an access token without refresh capability."""
    
    def __init__(self, access_token: str):
        super().__init__()
        self.token = access_token
    
    def refresh(self, request: Request):
        """This credential type doesn't support refresh."""
        pass
    
    def before_request(self, request, method, url, headers):
        """Add the access token to the request headers."""
        headers['Authorization'] = f'Bearer {self.token}'


def get_analytics_service(
    service_name: str,
    access_token: Optional[str] = None,
    version: str = "v1beta"
):
    """
    Get authenticated Google Analytics API service.
    
    Args:
        service_name: Name of the service ('analyticsdata' or 'analyticsadmin')
        access_token: OAuth access token from FastMCP GoogleProvider
        version: API version (default: 'v1beta')
        
    Returns:
        Authenticated Google Analytics API service
        
    Raises:
        ValueError: If no access token is provided
    """
    if not access_token:
        raise ValueError(f"Access token is required for Google Analytics {service_name} API")
    
    # Create credentials from access token
    credentials = AccessTokenCredentials(access_token)
    
    # Build and return the Analytics API service
    service = build(service_name, version, credentials=credentials)
    return service

