"""
Google Workspace OAuth Scopes

This module centralizes OAuth scope definitions for Google Workspace integration.
Separated from service_decorator.py to avoid circular imports.
"""
import logging
from typing import Dict

logger = logging.getLogger(__name__)

# Temporary map to associate OAuth state with MCP session ID
# This should ideally be a more robust cache in a production system (e.g., Redis)
OAUTH_STATE_TO_SESSION_ID_MAP: Dict[str, str] = {}

# Individual OAuth Scope Constants
USERINFO_EMAIL_SCOPE = 'https://www.googleapis.com/auth/userinfo.email'
OPENID_SCOPE = 'openid'

# Google Analytics 4 scopes
GOOGLE_ANALYTICS_READONLY_SCOPE = 'https://www.googleapis.com/auth/analytics.readonly'
GOOGLE_ANALYTICS_EDIT_SCOPE = 'https://www.googleapis.com/auth/analytics.edit'
GOOGLE_ANALYTICS_MANAGE_USERS_SCOPE = 'https://www.googleapis.com/auth/analytics.manage.users'
GOOGLE_ANALYTICS_MANAGE_USERS_READONLY_SCOPE = 'https://www.googleapis.com/auth/analytics.manage.users.readonly'
GOOGLE_ANALYTICS_PROVISION_SCOPE = 'https://www.googleapis.com/auth/analytics.provision'


# Base OAuth scopes required for user identification
BASE_SCOPES = [
    USERINFO_EMAIL_SCOPE,
    OPENID_SCOPE
]

GOOGLE_ANALYTICS_SCOPES = [
    GOOGLE_ANALYTICS_READONLY_SCOPE,
    GOOGLE_ANALYTICS_EDIT_SCOPE,
    GOOGLE_ANALYTICS_MANAGE_USERS_SCOPE,
    GOOGLE_ANALYTICS_MANAGE_USERS_READONLY_SCOPE,
    GOOGLE_ANALYTICS_PROVISION_SCOPE
]

# Combined scopes for all supported Google Workspace operations
SCOPES = list(set(BASE_SCOPES + GOOGLE_ANALYTICS_SCOPES))