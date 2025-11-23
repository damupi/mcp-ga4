"""Google Analytics MCP Server - Tools Module

This module implements MCP tools for Google Analytics Data API v1beta and Admin API v1beta.
"""

from typing import Any, Dict, List, Optional

from fastmcp.server.dependencies import get_access_token
from fastmcp import Context

from .auth import get_analytics_service
from .utils import (
    build_dimension_filter,
    build_metric_aggregation,
    format_error_message,
    format_report_response,
    parse_account_name,
    parse_property_name,
    validate_date,
)


# ============================================================================
# ANALYTICS DATA API TOOLS
# ============================================================================


async def run_report(
    property_id: str,
    start_date: str,
    end_date: str,
    dimensions: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
    dimension_filter: Optional[Dict[str, Any]] = None,
    limit: int = 10,
    offset: int = 0,
    ctx: Optional[Context] = None,
) -> str:
    """
    Run analytics reports with dimensions, metrics, and filters.
    
    Args:
        property_id: GA4 property ID (e.g., "123456789")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dimensions: List of dimension names (e.g., ["date", "country"])
        metrics: List of metric names (e.g., ["activeUsers", "sessions"])
        dimension_filter: Optional FilterExpression for filtering
                         https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/FilterExpression
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with formatted report data
    """
    try:
        # Validate dates
        if not validate_date(start_date) or not validate_date(end_date):
            raise ValueError("Dates must be in YYYY-MM-DD format")
        

        if ctx:
            ctx.info(f"Running report for property {property_id} ({start_date} to {end_date})")

        token = get_access_token()
        # Extract raw token string from AccessToken object
        if hasattr(token, 'token'):
            access_token = token.token
        else:
            access_token = str(token)

        if ctx:
            ctx.info(f"Got access token for report (type: {type(token)})")
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Build request body
        request_body = {
            "dateRanges": [{"startDate": start_date, "endDate": end_date}],
            "limit": limit,
            "offset": offset,
        }
        
        # Add dimensions if provided
        if dimensions:
            request_body["dimensions"] = [{"name": dim} for dim in dimensions]
        
        # Add metrics if provided (default to activeUsers if not specified)
        if metrics:
            request_body["metrics"] = build_metric_aggregation(metrics)
        else:
            request_body["metrics"] = [{"name": "activeUsers"}]
        
        # Add dimension filter if provided
        if dimension_filter:
            request_body["dimensionFilter"] = dimension_filter
        
        # Execute the request
        property_name = f"properties/{property_id}"
        response = service.properties().runReport(
            property=property_name,
            body=request_body
        ).execute()
        
        # Format and return response
        formatted = format_report_response(response)
        
        import json
        return json.dumps({
            "property_id": property_id,
            "date_range": f"{start_date} to {end_date}",
            "data": formatted
        }, indent=2)
        
    except Exception as e:
        if ctx:
            ctx.error(f"Error in run_report: {e}")
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def run_realtime_report(
    property_id: str,
    dimensions: Optional[List[str]] = None,
    metrics: Optional[List[str]] = None,
    limit: int = 10,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get real-time analytics data (last 30 minutes).
    
    Args:
        property_id: GA4 property ID
        dimensions: List of dimension names
        metrics: List of metric names
        limit: Maximum number of rows to return
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with real-time data
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Build request body
        request_body = {
            "limit": limit,
        }
        
        # Add dimensions if provided
        if dimensions:
            request_body["dimensions"] = [{"name": dim} for dim in dimensions]
        
        # Add metrics if provided (default to activeUsers)
        if metrics:
            request_body["metrics"] = build_metric_aggregation(metrics)
        else:
            request_body["metrics"] = [{"name": "activeUsers"}]
        
        # Execute the request
        property_name = f"properties/{property_id}"
        response = service.properties().runRealtimeReport(
            property=property_name,
            body=request_body
        ).execute()
        
        # Format and return response
        formatted = format_report_response(response)
        
        import json
        return json.dumps({
            "property_id": property_id,
            "realtime_data": formatted,
            "note": "Data from last 30 minutes"
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def list_dimensions(
    property_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get available dimensions with descriptions.
    
    Args:
        property_id: GA4 property ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with list of dimensions
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get metadata
        property_name = f"properties/{property_id}"
        response = service.properties().getMetadata(
            name=f"{property_name}/metadata"
        ).execute()
        
        # Extract dimensions
        dimensions = []
        for dimension in response.get("dimensions", []):
            dimensions.append({
                "api_name": dimension.get("apiName"),
                "ui_name": dimension.get("uiName"),
                "description": dimension.get("description"),
                "category": dimension.get("category"),
            })
        
        import json
        return json.dumps({
            "property_id": property_id,
            "dimensions": dimensions,
            "total": len(dimensions)
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def list_metrics(
    property_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get available metrics with descriptions.
    
    Args:
        property_id: GA4 property ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with list of metrics
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsdata', access_token)
        
        # Get metadata
        property_name = f"properties/{property_id}"
        response = service.properties().getMetadata(
            name=f"{property_name}/metadata"
        ).execute()
        
        # Extract metrics
        metrics = []
        for metric in response.get("metrics", []):
            metrics.append({
                "api_name": metric.get("apiName"),
                "ui_name": metric.get("uiName"),
                "description": metric.get("description"),
                "category": metric.get("category"),
                "type": metric.get("type"),
            })
        
        import json
        return json.dumps({
            "property_id": property_id,
            "metrics": metrics,
            "total": len(metrics)
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


# ============================================================================
# ANALYTICS ADMIN API TOOLS
# ============================================================================


async def list_accounts(
    ctx: Optional[Context] = None,
) -> str:
    """
    List all GA4 accounts accessible to the user.
    
    Args:
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with list of accounts
    """
    try:
        if ctx:
            ctx.info("Listing accounts via tools")

        token = get_access_token()
        # Extract raw token string from AccessToken object
        if hasattr(token, 'token'):
            access_token = token.token
        else:
            access_token = str(token)

        if ctx:
            ctx.info(f"Got access token for list_accounts (type: {type(token)})")
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # List accounts
        response = service.accounts().list().execute()
        
        accounts = []
        for account in response.get("accounts", []):
            account_id = parse_account_name(account.get("name", ""))
            accounts.append({
                "account_id": account_id,
                "name": account.get("displayName"),
                "create_time": account.get("createTime"),
                "update_time": account.get("updateTime"),
            })
        
        import json
        return json.dumps({
            "accounts": accounts,
            "total": len(accounts)
        }, indent=2)
        
    except Exception as e:
        if ctx:
            ctx.error(f"Error in list_accounts: {e}")
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def list_properties(
    account_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    List all GA4 properties for an account.
    
    Args:
        account_id: Account ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with list of properties
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # List properties with filter
        filter_str = f"parent:accounts/{account_id}"
        response = service.properties().list(filter=filter_str).execute()
        
        properties = []
        for prop in response.get("properties", []):
            property_id = parse_property_name(prop.get("name", ""))
            properties.append({
                "property_id": property_id,
                "name": prop.get("displayName"),
                "time_zone": prop.get("timeZone"),
                "currency_code": prop.get("currencyCode"),
                "create_time": prop.get("createTime"),
                "update_time": prop.get("updateTime"),
            })
        
        import json
        return json.dumps({
            "account_id": account_id,
            "properties": properties,
            "total": len(properties)
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_property(
    property_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get property details.
    
    Args:
        property_id: Property ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with property details
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # Get property
        property_name = f"properties/{property_id}"
        response = service.properties().get(name=property_name).execute()
        
        import json
        return json.dumps({
            "property_id": property_id,
            "name": response.get("displayName"),
            "time_zone": response.get("timeZone"),
            "currency_code": response.get("currencyCode"),
            "industry_category": response.get("industryCategory"),
            "create_time": response.get("createTime"),
            "update_time": response.get("updateTime"),
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def list_data_streams(
    property_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    List data streams for a property.
    
    Args:
        property_id: Property ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with list of data streams
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # List data streams
        parent = f"properties/{property_id}"
        response = service.properties().dataStreams().list(parent=parent).execute()
        
        streams = []
        for stream in response.get("dataStreams", []):
            stream_data = {
                "stream_id": stream.get("name", "").split("/")[-1],
                "name": stream.get("displayName"),
                "type": stream.get("type"),
                "create_time": stream.get("createTime"),
                "update_time": stream.get("updateTime"),
            }
            
            # Add type-specific data
            if "webStreamData" in stream:
                stream_data["web_data"] = {
                    "measurement_id": stream["webStreamData"].get("measurementId"),
                    "default_uri": stream["webStreamData"].get("defaultUri"),
                }
            elif "androidAppStreamData" in stream:
                stream_data["android_data"] = {
                    "package_name": stream["androidAppStreamData"].get("packageName"),
                }
            elif "iosAppStreamData" in stream:
                stream_data["ios_data"] = {
                    "bundle_id": stream["iosAppStreamData"].get("bundleId"),
                }
            
            streams.append(stream_data)
        
        import json
        return json.dumps({
            "property_id": property_id,
            "data_streams": streams,
            "total": len(streams)
        }, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)


async def get_data_stream(
    property_id: str,
    stream_id: str,
    ctx: Optional[Context] = None,
) -> str:
    """
    Get data stream details.
    
    Args:
        property_id: Property ID
        stream_id: Data stream ID
        ctx: FastMCP context for logging
        
    Returns:
        JSON string with data stream details
    """
    try:
        token = get_access_token()
        access_token = str(token)
        
        service = get_analytics_service('analyticsadmin', access_token)
        
        # Get data stream
        stream_name = f"properties/{property_id}/dataStreams/{stream_id}"
        response = service.properties().dataStreams().get(name=stream_name).execute()
        
        stream_data = {
            "stream_id": stream_id,
            "property_id": property_id,
            "name": response.get("displayName"),
            "type": response.get("type"),
            "create_time": response.get("createTime"),
            "update_time": response.get("updateTime"),
        }
        
        # Add type-specific data
        if "webStreamData" in response:
            stream_data["web_data"] = {
                "measurement_id": response["webStreamData"].get("measurementId"),
                "firebase_app_id": response["webStreamData"].get("firebaseAppId"),
                "default_uri": response["webStreamData"].get("defaultUri"),
            }
        elif "androidAppStreamData" in response:
            stream_data["android_data"] = {
                "package_name": response["androidAppStreamData"].get("packageName"),
                "firebase_app_id": response["androidAppStreamData"].get("firebaseAppId"),
            }
        elif "iosAppStreamData" in response:
            stream_data["ios_data"] = {
                "bundle_id": response["iosAppStreamData"].get("bundleId"),
                "firebase_app_id": response["iosAppStreamData"].get("firebaseAppId"),
            }
        
        import json
        return json.dumps(stream_data, indent=2)
        
    except Exception as e:
        import json
        return json.dumps({
            "error": format_error_message(e)
        }, indent=2)
