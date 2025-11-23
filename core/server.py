import logging
import os
from typing import Optional
from importlib import metadata

from fastapi import Header
from fastapi.responses import HTMLResponse

from mcp import types

from mcp.server.fastmcp import FastMCP
from starlette.requests import Request

from auth.google_auth import handle_auth_callback, start_auth_flow, check_client_secrets
from auth.oauth_callback_server import get_oauth_redirect_uri, ensure_oauth_callback_available
from auth.oauth_responses import create_error_response, create_success_response, create_server_error_response

# Import shared configuration
from auth.scopes import (
    OAUTH_STATE_TO_SESSION_ID_MAP,
    USERINFO_EMAIL_SCOPE,
    OPENID_SCOPE,
    GOOGLE_ANALYTICS_READONLY_SCOPE,
    GOOGLE_ANALYTICS_EDIT_SCOPE,
    GOOGLE_ANALYTICS_MANAGE_USERS_SCOPE,
    GOOGLE_ANALYTICS_MANAGE_USERS_READONLY_SCOPE,
    GOOGLE_ANALYTICS_PROVISION_SCOPE,
    SCOPES
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

WORKSPACE_MCP_PORT = int(os.getenv("PORT", os.getenv("WORKSPACE_MCP_PORT", 8000)))
WORKSPACE_MCP_BASE_URI = os.getenv("WORKSPACE_MCP_BASE_URI", "http://localhost")
USER_GOOGLE_EMAIL = os.getenv("USER_GOOGLE_EMAIL", None)

# Transport mode detection (will be set by main.py)
_current_transport_mode = "stdio"  # Default to stdio

# Basic MCP server instance
server = FastMCP(
    name="google_workspace",
    server_url=f"{WORKSPACE_MCP_BASE_URI}:{WORKSPACE_MCP_PORT}/mcp",
    port=WORKSPACE_MCP_PORT,
    host="0.0.0.0"
)

def set_transport_mode(mode: str):
    """Set the current transport mode for OAuth callback handling."""
    global _current_transport_mode
    _current_transport_mode = mode
    logger.info(f"Transport mode set to: {mode}")

def get_oauth_redirect_uri_for_current_mode() -> str:
    """Get OAuth redirect URI based on current transport mode."""
    return get_oauth_redirect_uri(WORKSPACE_MCP_PORT, WORKSPACE_MCP_BASE_URI)

# Health check endpoint
@server.custom_route("/health", methods=["GET"])
async def health_check(request: Request):
    """Health check endpoint for container orchestration."""
    from fastapi.responses import JSONResponse
    try:
        version = metadata.version("workspace-mcp")
    except metadata.PackageNotFoundError:
        version = "dev"
    return JSONResponse({
        "status": "healthy",
        "service": "workspace-mcp",
        "version": version,
        "transport": _current_transport_mode
    })


@server.custom_route("/oauth2callback", methods=["GET"])
async def oauth2_callback(request: Request) -> HTMLResponse:
    """
    Handle OAuth2 callback from Google via a custom route.
    This endpoint exchanges the authorization code for credentials and saves them.
    It then displays a success or error page to the user.
    """
    state = request.query_params.get("state")
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        error_message = f"Authentication failed: Google returned an error: {error}. State: {state}."
        logger.error(error_message)
        return create_error_response(error_message)

    if not code:
        error_message = "Authentication failed: No authorization code received from Google."
        logger.error(error_message)
        return create_error_response(error_message)

    try:
        # Check if we have credentials available (environment variables or file)
        error_message = check_client_secrets()
        if error_message:
            return create_server_error_response(error_message)

        logger.info(f"OAuth callback: Received code (state: {state}). Attempting to exchange for tokens.")

        mcp_session_id: Optional[str] = OAUTH_STATE_TO_SESSION_ID_MAP.pop(state, None)
        if mcp_session_id:
            logger.info(f"OAuth callback: Retrieved MCP session ID '{mcp_session_id}' for state '{state}'.")
        else:
            logger.warning(f"OAuth callback: No MCP session ID found for state '{state}'. Auth will not be tied to a specific session directly via this callback.")

        # Exchange code for credentials. handle_auth_callback will save them.
        # The user_id returned here is the Google-verified email.
        verified_user_id, credentials = handle_auth_callback(
            scopes=SCOPES, # Ensure all necessary scopes are requested
            authorization_response=str(request.url),
            redirect_uri=get_oauth_redirect_uri_for_current_mode(),
            session_id=mcp_session_id # Pass session_id if available
        )

        log_session_part = f" (linked to session: {mcp_session_id})" if mcp_session_id else ""
        logger.info(f"OAuth callback: Successfully authenticated user: {verified_user_id} (state: {state}){log_session_part}.")

        # Return success page using shared template
        return create_success_response(verified_user_id)

    except Exception as e:
        error_message_detail = f"Error processing OAuth callback (state: {state}): {str(e)}"
        logger.error(error_message_detail, exc_info=True)
        # Generic error page for any other issues during token exchange or credential saving
        return create_server_error_response(str(e))

@server.tool()
async def start_google_auth(
    service_name: str,
    user_google_email: str = USER_GOOGLE_EMAIL,
    mcp_session_id: Optional[str] = Header(None, alias="Mcp-Session-Id")
) -> str:
    """
    Initiates the Google OAuth 2.0 authentication flow for the specified user email and service.
    This is the primary method to establish credentials when no valid session exists or when targeting a specific account for a particular service.
    It generates an authorization URL that the LLM must present to the user.
    The authentication attempt is linked to the current MCP session via `mcp_session_id`.

    LLM Guidance:
    - Use this tool when you need to authenticate a user for a specific Google service (e.g., "Google Calendar", "Google Docs", "Gmail", "Google Drive")
      and don't have existing valid credentials for the session or specified email.
    - You MUST provide the `user_google_email` and the `service_name`. If you don't know the email, ask the user first.
    - Valid `service_name` values include "ga4", "gmail", "drive", "calendar", "docs" or their descriptive forms like "Google Analytics 4", "Google Calendar", etc.
    - After calling this tool, present the returned authorization URL clearly to the user and instruct them to:
        1. Click the link and complete the sign-in/consent process in their browser.
        2. Note the authenticated email displayed on the success page.
        3. Provide that email back to you (the LLM).
        4. Retry their original request, including the confirmed `user_google_email`.

    Args:
        user_google_email (str): The user's full Google email address (e.g., 'example@gmail.com'). This is REQUIRED.
        service_name (str): The name of the Google service for which authentication is being requested (e.g., "Google Calendar", "Google Docs"). This is REQUIRED.
        mcp_session_id (Optional[str]): The active MCP session ID (automatically injected by FastMCP from the Mcp-Session-Id header). Links the OAuth flow state to the session.

    Returns:
        str: A detailed message for the LLM with the authorization URL and instructions to guide the user through the authentication process.
    """
    if not user_google_email or not isinstance(user_google_email, str) or '@' not in user_google_email:
        error_msg = "Invalid or missing 'user_google_email'. This parameter is required and must be a valid email address. LLM, please ask the user for their Google email address."
        logger.error(f"[start_google_auth] {error_msg}")
        raise Exception(error_msg)

    if not service_name or not isinstance(service_name, str):
        error_msg = "Invalid or missing 'service_name'. This parameter is required (e.g., 'Google Calendar', 'Google Docs'). LLM, please specify the service name."
        logger.error(f"[start_google_auth] {error_msg}")
        raise Exception(error_msg)

    logger.info(f"Tool 'start_google_auth' invoked for user_google_email: '{user_google_email}', service: '{service_name}', session: '{mcp_session_id}'.")

    # Map service codes to descriptive names
    service_display_names = {
        "ga4": "Google Analytics 4",
        "gmail": "Gmail",
        "drive": "Google Drive",
        "calendar": "Google Calendar",
        "docs": "Google Docs"
    }
    
    # Use descriptive name if available, otherwise use the provided service_name
    display_service_name = service_display_names.get(service_name, service_name)

    # Ensure OAuth callback is available for current transport mode
    redirect_uri = get_oauth_redirect_uri_for_current_mode()
    if not ensure_oauth_callback_available(_current_transport_mode, WORKSPACE_MCP_PORT, WORKSPACE_MCP_BASE_URI):
        raise Exception("Failed to start OAuth callback server. Please try again.")

    auth_result = await start_auth_flow(
        mcp_session_id=mcp_session_id,
        user_google_email=user_google_email,
        service_name=display_service_name,
        redirect_uri=redirect_uri
    )
    return auth_result