"""Google Analytics MCP Server - Resources Module

This module implements MCP resources for read-only data access.
"""
from fastmcp.server.dependencies import get_access_token
from fastmcp import Context

from typing import Optional

from .auth import get_analytics_service
from .utils import (
    decode_account_property_id,
    format_error_message,
    format_report_response,
    get_date_range,
    parse_account_name,
    parse_property_name,
)




async def get_accounts_list(ctx: Context = None) -> str:
    """
    Resource: ga://accounts
    List all GA4 accounts accessible to the user.
    
    Returns:
        JSON string with list of accounts
    """
    try:
        if ctx:
            ctx.info("Requesting access token for ga://accounts")

        token = get_access_token()
        # Extract raw token string from AccessToken object
        if hasattr(token, 'token'):
            access_token = token.token
        else:
            access_token = str(token)
        
        if ctx:
            ctx.info(f"Got access token (type: {type(token)})")
            # Be careful not to log the full token in production, but for debugging it's useful
            # ctx.debug(f"Token: {access_token[:10]}...")  
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # List accounts
        if ctx:
            ctx.info("Calling Google Analytics Admin API: accounts.list")
            
        response = service.accounts().list().execute()
        
        accounts = []
        for account in response.get("accounts", []):
            account_id = parse_account_name(account.get("name", ""))
            accounts.append({
                "account_id": account_id,
                "name": account.get("displayName"),
                "create_time": account.get("createTime"),
            })
        
        if ctx:
            ctx.info(f"Found {len(accounts)} accounts")

        import json
        return json.dumps({
            "accounts": accounts,
            "total": len(accounts)
        }, indent=2)
        
    except Exception as e:
        if ctx:
            ctx.error(f"Error in get_accounts_list: {e}")
            
        import json
        token_preview = "None"
        if 'access_token' in locals() and access_token:
            token_preview = f"{access_token[:10]}... (len={len(access_token)})"
            
        return json.dumps({
            "error": format_error_message(e),
            "debug_token_info": {
                "type": str(type(token)) if 'token' in locals() else "Not defined",
                "preview": token_preview
            }
        }, indent=2)


async def get_account_properties(account_id: str) -> str:
    """
    Resource: ga://accounts/{account_id}/properties
    List all properties for a specific account.
    
    Args:
        account_id: Account ID (URL-encoded)
        
    Returns:
        JSON string with list of properties
    """
    try:
        # Decode account ID
        decoded_account_id = decode_account_property_id(account_id)
        
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # List properties
        filter_str = f"parent:accounts/{decoded_account_id}"
        response = service.properties().list(filter=filter_str).execute()
        
        properties = []
        for prop in response.get("properties", []):
            property_id = parse_property_name(prop.get("name", ""))
            properties.append({
                "property_id": property_id,
                "name": prop.get("displayName"),
                "time_zone": prop.get("timeZone"),
                "currency_code": prop.get("currencyCode"),
            })
        
        import json
        return json.dumps({
            "account_id": decoded_account_id,
            "properties": properties,
            "total": len(properties)
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_config() -> str:
    """
    Resource: ga://config
    Get server configuration and status.
    
    Returns:
        JSON string with server configuration
    """
    import json
    return json.dumps({
        "server": "Google Analytics MCP",
        "version": "0.1.0",
        "api_versions": {
            "analytics_data": "v1beta",
            "analytics_admin": "v1beta"
        },
        "authentication": "Google OAuth 2.0 (FastMCP)",
        "scopes": [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/analytics.readonly"
        ]
    }, indent=2)


async def get_analytics_summary(account_id: str, property_id: str) -> str:
    """
    Resource: ga://accounts/{account_id}/properties/{property_id}/summary
    Get recent analytics summary for a property (last 28 days).
    
    Args:
        account_id: Account ID (URL-encoded)
        property_id: Property ID (URL-encoded)
        
    Returns:
        JSON string with analytics summary
    """
    try:
        # Decode IDs
        decoded_property_id = decode_account_property_id(property_id)
        decoded_account_id = decode_account_property_id(account_id)
        
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get last 28 days of data
        start_date, end_date = get_date_range(28)
        
        request_body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "metrics": [
                {"name": "activeUsers"},
                {"name": "sessions"},
                {"name": "screenPageViews"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
            ],
        }
        
        property_name = f"properties/{decoded_property_id}"
        response = service.properties().runReport(
            property=property_name,
            body=request_body
        ).execute()
        
        # Extract totals
        summary = {
            "account_id": decoded_account_id,
            "property_id": decoded_property_id,
            "period": f"{start_date} to {end_date}",
            "active_users": 0,
            "sessions": 0,
            "page_views": 0,
            "bounce_rate": 0.0,
            "avg_session_duration": 0.0,
        }
        
        if "rows" in response and len(response["rows"]) > 0:
            row = response["rows"][0]
            metrics = row.get("metricValues", [])
            if len(metrics) >= 5:
                summary["active_users"] = int(float(metrics[0].get("value", 0)))
                summary["sessions"] = int(float(metrics[1].get("value", 0)))
                summary["page_views"] = int(float(metrics[2].get("value", 0)))
                summary["bounce_rate"] = round(float(metrics[3].get("value", 0)), 2)
                summary["avg_session_duration"] = round(float(metrics[4].get("value", 0)), 2)
        
        import json
        return json.dumps(summary, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_top_pages(account_id: str, property_id: str) -> str:
    """
    Resource: ga://accounts/{account_id}/properties/{property_id}/top-pages
    Get top 10 pages for a property (last 7 days).
    
    Args:
        account_id: Account ID (URL-encoded)
        property_id: Property ID (URL-encoded)
        
    Returns:
        JSON string with top pages
    """
    try:
        # Decode IDs
        decoded_property_id = decode_account_property_id(property_id)
        decoded_account_id = decode_account_property_id(account_id)
        
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get last 7 days of data
        start_date, end_date = get_date_range(7)
        
        request_body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "screenPageViews"},
            ],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": 10,
        }
        
        property_name = f"properties/{decoded_property_id}"
        response = service.properties().runReport(
            property=property_name,
            body=request_body
        ).execute()
        
        formatted = format_report_response(response)
        
        import json
        return json.dumps({
            "account_id": decoded_account_id,
            "property_id": decoded_property_id,
            "period": f"{start_date} to {end_date}",
            "top_pages": formatted["rows"]
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_top_sources(account_id: str, property_id: str) -> str:
    """
    Resource: ga://accounts/{account_id}/properties/{property_id}/top-sources
    Get top 10 traffic sources for a property (last 7 days).
    
    Args:
        account_id: Account ID (URL-encoded)
        property_id: Property ID (URL-encoded)
        
    Returns:
        JSON string with top traffic sources
    """
    try:
        # Decode IDs
        decoded_property_id = decode_account_property_id(property_id)
        decoded_account_id = decode_account_property_id(account_id)
        
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get last 7 days of data
        start_date, end_date = get_date_range(7)
        
        request_body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "dimensions": [
                {"name": "sessionSource"},
                {"name": "sessionMedium"}
            ],
            "metrics": [
                {"name": "sessions"},
                {"name": "activeUsers"},
            ],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": 10,
        }
        
        property_name = f"properties/{decoded_property_id}"
        response = service.properties().runReport(
            property=property_name,
            body=request_body
        ).execute()
        
        formatted = format_report_response(response)
        
        import json
        return json.dumps({
            "account_id": decoded_account_id,
            "property_id": decoded_property_id,
            "period": f"{start_date} to {end_date}",
            "top_sources": formatted["rows"]
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_realtime_data(account_id: str, property_id: str) -> str:
    """
    Resource: ga://accounts/{account_id}/properties/{property_id}/realtime
    Get real-time analytics data for a property.
    
    Args:
        account_id: Account ID (URL-encoded)
        property_id: Property ID (URL-encoded)
        
    Returns:
        JSON string with real-time data
    """
    try:
        # Decode IDs
        decoded_property_id = decode_account_property_id(property_id)
        decoded_account_id = decode_account_property_id(account_id)
        
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get active users
        request_body = {
            "metrics": [{"name": "activeUsers"}],
        }
        
        property_name = f"properties/{decoded_property_id}"
        response = service.properties().runRealtimeReport(
            property=property_name,
            body=request_body
        ).execute()
        
        active_users = 0
        if "rows" in response and len(response["rows"]) > 0:
            active_users = int(float(response["rows"][0]["metricValues"][0].get("value", 0)))
        
        # Get top pages in real-time
        request_body_pages = {
            "dimensions": [{"name": "unifiedScreenName"}],
            "metrics": [{"name": "activeUsers"}],
            "orderBys": [{"metric": {"metricName": "activeUsers"}, "desc": True}],
            "limit": 5,
        }
        
        response_pages = service.properties().runRealtimeReport(
            property=property_name,
            body=request_body_pages
        ).execute()
        
        formatted_pages = format_report_response(response_pages)
        
        import json
        return json.dumps({
            "account_id": decoded_account_id,
            "property_id": decoded_property_id,
            "active_users": active_users,
            "top_pages_now": formatted_pages["rows"],
            "note": "Data from last 30 minutes"
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)
