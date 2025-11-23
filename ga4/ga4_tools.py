"""
Google Analytics 4 (GA4) MCP Tools

This module provides MCP tools for interacting with the Google Analytics 4 API.
"""

import logging
import asyncio
from typing import Optional, List, Dict, Any, Literal
from datetime import datetime, timedelta

from mcp import types
from fastapi import Body

from auth.service_decorator import require_google_service
from core.utils import handle_http_errors
from core.server import server

logger = logging.getLogger(__name__)


def _format_date_range(start_date: str, end_date: str) -> tuple[str, str]:
    """
    Format date range for GA4 API requests.
    
    Args:
        start_date: Start date in YYYY-MM-DD format or relative format like '7daysAgo'
        end_date: End date in YYYY-MM-DD format or relative format like 'today'
        
    Returns:
        Tuple of (formatted_start_date, formatted_end_date)
    """
    # GA4 API accepts both YYYY-MM-DD and relative dates like '7daysAgo', 'yesterday', 'today'
    return start_date, end_date


def _format_metrics_and_dimensions(metrics: List[str], dimensions: List[str]) -> tuple[List[Dict], List[Dict]]:
    """
    Format metrics and dimensions for GA4 API requests.
    
    Args:
        metrics: List of metric names
        dimensions: List of dimension names
        
    Returns:
        Tuple of (formatted_metrics, formatted_dimensions)
    """
    formatted_metrics = [{"name": metric} for metric in metrics]
    formatted_dimensions = [{"name": dimension} for dimension in dimensions]
    
    return formatted_metrics, formatted_dimensions


def _build_filter_expression(filter_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a FilterExpression object from a filter configuration.
    
    Args:
        filter_config: Dictionary containing filter configuration
        
    Returns:
        FilterExpression dictionary
    """
    filter_type = filter_config.get("type", "string")
    field_name = filter_config.get("field_name", "")
    
    # Build the individual filter
    filter_obj = {"fieldName": field_name}
    
    if filter_type == "string":
        match_type = filter_config.get("match_type", "EXACT")
        value = filter_config.get("value", "")
        case_sensitive = filter_config.get("case_sensitive", True)
        
        filter_obj["stringFilter"] = {
            "matchType": match_type,
            "value": value,
            "caseSensitive": case_sensitive
        }
    
    elif filter_type == "in_list":
        values = filter_config.get("values", [])
        case_sensitive = filter_config.get("case_sensitive", True)
        
        filter_obj["inListFilter"] = {
            "values": values,
            "caseSensitive": case_sensitive
        }
    
    elif filter_type == "numeric":
        operation = filter_config.get("operation", "EQUAL")
        value = filter_config.get("value", 0)
        
        numeric_value = {}
        if isinstance(value, int):
            numeric_value["int64Value"] = str(value)
        else:
            numeric_value["doubleValue"] = float(value)
        
        filter_obj["numericFilter"] = {
            "operation": operation,
            "value": numeric_value
        }
    
    elif filter_type == "between":
        from_value = filter_config.get("from_value", 0)
        to_value = filter_config.get("to_value", 0)
        
        from_numeric = {}
        if isinstance(from_value, int):
            from_numeric["int64Value"] = str(from_value)
        else:
            from_numeric["doubleValue"] = float(from_value)
        
        to_numeric = {}
        if isinstance(to_value, int):
            to_numeric["int64Value"] = str(to_value)
        else:
            to_numeric["doubleValue"] = float(to_value)
        
        filter_obj["betweenFilter"] = {
            "fromValue": from_numeric,
            "toValue": to_numeric
        }
    
    elif filter_type == "empty":
        filter_obj["emptyFilter"] = {}
    
    return {"filter": filter_obj}


def _build_and_group_filter(filters: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build an AND group filter expression from a list of filters.
    
    Args:
        filters: List of filter configurations
        
    Returns:
        FilterExpression with andGroup
    """
    if not filters:
        return {}
    
    if len(filters) == 1:
        return _build_filter_expression(filters[0])
    
    expressions = [_build_filter_expression(f) for f in filters]
    
    return {
        "andGroup": {
            "expressions": expressions
        }
    }


def _build_not_filter(filter_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a NOT filter expression from a filter configuration.
    
    Args:
        filter_config: Filter configuration to negate
        
    Returns:
        FilterExpression with notExpression
    """
    return {
        "notExpression": _build_filter_expression(filter_config)
    }


def _format_report_results(response: Dict[str, Any]) -> str:
    """
    Format GA4 report results into a readable string.
    
    Args:
        response: GA4 API response
        
    Returns:
        Formatted string with results
    """
    if not response:
        return "No data returned from GA4 API"
    
    reports = response.get("reports", [])
    if not reports:
        return "No reports found in response"
    
    result_lines = []
    
    for i, report in enumerate(reports):
        if i > 0:
            result_lines.append("\n" + "="*50)
        
        # Get column headers
        column_header = report.get("columnHeader", {})
        dimensions = column_header.get("dimensions", [])
        metrics = [metric.get("name") for metric in column_header.get("metricHeader", {}).get("metricHeaderEntries", [])]
        
        # Format headers
        headers = dimensions + metrics
        if headers:
            result_lines.append("Headers: " + " | ".join(headers))
            result_lines.append("-" * 50)
        
        # Format rows
        rows = report.get("data", {}).get("rows", [])
        if not rows:
            result_lines.append("No data rows found")
            continue
            
        for row in rows:
            row_values = []
            
            # Add dimension values
            dimension_values = row.get("dimensions", [])
            row_values.extend(dimension_values)
            
            # Add metric values
            metric_values = row.get("metrics", [])
            for metric in metric_values:
                values = metric.get("values", [])
                row_values.extend(values)
            
            if row_values:
                result_lines.append(" | ".join(row_values))
    
    return "\n".join(result_lines)


@server.tool()
@require_google_service("ga4_admin", "ga4_read")
@handle_http_errors("list_ga4_accounts")
async def list_ga4_accounts(
    service, 
    user_google_email: str
) -> str:
    """
    Retrieves all GA4 accounts accessible by the authenticated user.
    
    Args:
        user_google_email (str): The user's Google email address. Required.
        
    Returns:
        str: A formatted list of GA4 accounts with their details.
    """
    logger.info(f"[list_ga4_accounts] Getting accounts for user: {user_google_email}")
    
    try:
        # List all accounts accessible to the authenticated user
        accounts = await asyncio.to_thread(
            service.accounts().list().execute
        )
        
        if not accounts or 'accounts' not in accounts:
            return "No GA4 accounts found for this user."
        
        result_lines = [
            f"GA4 Accounts for {user_google_email}:",
            "=" * 40
        ]
        
        for account in accounts['accounts']:
            account_id = account.get('name', 'Unknown').replace('accounts/', '')
            display_name = account.get('displayName', 'Unknown')
            create_time = account.get('createTime', 'Unknown')
            
            result_lines.extend([
                f"Account ID: {account_id}",
                f"Display Name: {display_name}",
                f"Created: {create_time}",
                "-" * 30
            ])
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"[list_ga4_accounts] Error: {str(e)}")
        return f"Error retrieving GA4 accounts: {str(e)}"


@server.tool()
@require_google_service("ga4_admin", "ga4_read")
@handle_http_errors("list_ga4_properties")
async def list_ga4_properties(
    service,
    user_google_email: str,
    filter_id: str,
    include_sub_properties: bool = True
) -> str:
    """
    Retrieves GA4 properties for the authenticated user.
    
    Args:
        user_google_email (str): The user's Google email address. Required.
        filter_id (str): Specific account ID or property ID to filter properties. If not provided return an error.
        include_account_properties (bool): Whether to include properties with parent:accounts/ filter. Default True.
        include_property_properties (bool): Whether to include sub-properties with parent:properties/ filter. Default True.
        
    Returns:
        str: A formatted list of GA4 properties with their details.
    """
    logger.info(f"[list_ga4_properties] Getting properties for user: {user_google_email}")
    
    try:
        all_properties = []
        
        # Handle account-based filtering
        if filter_id:
            if filter_id:
                # Filter by specific account ID
                filter_str = f"parent:accounts/{filter_id}"
                logger.info(f"[list_ga4_properties] Fetching with filter: {filter_str}")
                account_properties = await asyncio.to_thread(
                    service.properties().list(filter=filter_str).execute
                )
                
                if account_properties and 'properties' in account_properties:
                    all_properties.extend(account_properties['properties'])
            else:
                # No account_id or property_id provided, return error
                logger.info(f"[list_ga4_properties] No account_id or property_id provided in filter_id field, returning error")
                return "Error: filter_id is required (account_id or property_id)"
             
        # Handle property-based filtering (sub-properties)
        if include_sub_properties and all_properties:
            logger.info(f"[list_ga4_properties] Fetching sub-properties for {len(all_properties)} properties")
            
            # For each property found, get its sub-properties
            for prop in all_properties[:]:  # Create a copy to iterate over
                property_id = prop.get('name', '').replace('properties/', '')
                if property_id:
                    filter_str = f"parent:properties/{property_id}"
                    logger.info(f"[list_ga4_properties] Fetching sub-properties with filter: {filter_str}")
                    
                    try:
                        sub_properties = await asyncio.to_thread(
                            service.properties().list(filter=filter_str).execute
                        )
                        
                        if sub_properties and 'properties' in sub_properties:
                            logger.info(f"[list_ga4_properties] Found {len(sub_properties['properties'])} sub-properties for property {property_id}")
                            all_properties.extend(sub_properties['properties'])
                        else:
                            logger.info(f"[list_ga4_properties] No sub-properties found for property {property_id}")
                    except Exception as sub_error:
                        logger.warning(f"[list_ga4_properties] Error fetching sub-properties for {property_id}: {str(sub_error)}")
                        # Continue with other properties even if one fails
                        continue
        
        if not all_properties:
            return "No GA4 properties found."
                 
        result_lines = [
            f"GA4 Properties for {user_google_email}:",
            "=" * 40
        ]
        
        for prop in all_properties:
            prop_id = prop.get('name', 'Unknown').replace('properties/', '')
            display_name = prop.get('displayName', 'Unknown')
            property_type = prop.get('propertyType', 'Unknown')
            currency_code = prop.get('currencyCode', 'Unknown')
            time_zone = prop.get('timeZone', 'Unknown')
            parent = prop.get('parent', 'Unknown')
            service_level = prop.get('serviceLevel', 'Unknown')
            
            # Determine if this is a main property or sub-property
            is_sub_property = parent.startswith('properties/')
            property_label = "Sub-Property" if is_sub_property else "Property"
            
            result_lines.extend([
                f"{property_label} ID: {prop_id}",
                f"Display Name: {display_name}",
                f"Property Type: {property_type}",
                f"Currency: {currency_code}",
                f"Time Zone: {time_zone}",
                f"Parent: {parent}",
                f"Service Level: {service_level}",
                "-" * 30
            ])
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"[list_ga4_properties] Error: {str(e)}")
        return f"Error retrieving GA4 properties: {str(e)}"


@server.tool()
@require_google_service("ga4_data", "ga4_read")
@handle_http_errors("run_ga4_report")
async def run_ga4_report(
    service,
    user_google_email: str,
    property_id: str,
    metrics: List[str] = Body(..., description="List of metrics to retrieve (e.g., ['activeUsers', 'sessions'])"),
    dimensions: List[str] = Body(default=[], description="List of dimensions to group by (e.g., ['country', 'city'])"),
    start_date: str = Body(default="7daysAgo", description="Start date (YYYY-MM-DD or relative like '7daysAgo')"),
    end_date: str = Body(default="today", description="End date (YYYY-MM-DD or relative like 'today')"),
    limit: int = Body(default=1000, description="Maximum number of rows to return"),
    dimension_filters: List[Dict[str, Any]] = Body(default=[], description="List of dimension filters to apply. Each filter should have 'field_name', 'type' (string/in_list/numeric/between/empty), and type-specific parameters"),
    metric_filters: List[Dict[str, Any]] = Body(default=[], description="List of metric filters to apply. Each filter should have 'field_name', 'type' (string/in_list/numeric/between/empty), and type-specific parameters"),
    not_dimension_filters: List[Dict[str, Any]] = Body(default=[], description="List of dimension filters to negate (NOT filters)"),
    not_metric_filters: List[Dict[str, Any]] = Body(default=[], description="List of metric filters to negate (NOT filters)")
) -> str:
    """
    Runs a GA4 report with specified metrics, dimensions, and filters.
    
    Args:
        user_google_email (str): The user's Google email address. Required.
        property_id (str): GA4 property ID (without 'properties/' prefix).
        metrics (List[str]): List of metrics to retrieve.
        dimensions (List[str]): List of dimensions to group by.
        start_date (str): Start date for the report.
        end_date (str): End date for the report.
        limit (int): Maximum number of rows to return.
        dimension_filters (List[Dict]): List of dimension filters to apply.
        metric_filters (List[Dict]): List of metric filters to apply.
        not_dimension_filters (List[Dict]): List of dimension filters to negate.
        not_metric_filters (List[Dict]): List of metric filters to negate.
        
    Filter format examples:
        String filter: {"field_name": "country", "type": "string", "match_type": "EXACT", "value": "US", "case_sensitive": true}
        In-list filter: {"field_name": "city", "type": "in_list", "values": ["New York", "Los Angeles"], "case_sensitive": true}
        Numeric filter: {"field_name": "sessions", "type": "numeric", "operation": "GREATER_THAN", "value": 100}
        Between filter: {"field_name": "sessions", "type": "between", "from_value": 10, "to_value": 100}
        Empty filter: {"field_name": "campaignName", "type": "empty"}
        
    Returns:
        str: Formatted report results.
    """
    logger.info(f"[run_ga4_report] Running report for property: {property_id}")
    
    try:
        # Format the property ID
        if not property_id.startswith('properties/'):
            property_id = f'properties/{property_id}'
        
        # Format dates
        formatted_start_date, formatted_end_date = _format_date_range(start_date, end_date)
        
        # Format metrics and dimensions
        formatted_metrics, formatted_dimensions = _format_metrics_and_dimensions(metrics, dimensions)
        
        # Build the request
        request_body = {
            "requests": [{
                "property": property_id,
                "dateRanges": [{
                    "startDate": formatted_start_date,
                    "endDate": formatted_end_date
                }],
                "metrics": formatted_metrics,
                "dimensions": formatted_dimensions,
                "limit": limit
            }]
        }
        
        # Add dimension filters if provided
        if dimension_filters or not_dimension_filters:
            all_dim_filters = []
            
            # Add regular dimension filters
            if dimension_filters:
                all_dim_filters.extend(dimension_filters)
            
            # Add negated dimension filters
            if not_dimension_filters:
                for not_filter in not_dimension_filters:
                    all_dim_filters.append({"not": True, **not_filter})
            
            if all_dim_filters:
                # Separate regular and NOT filters
                regular_filters = [f for f in all_dim_filters if not f.get("not", False)]
                not_filters = [f for f in all_dim_filters if f.get("not", False)]
                
                filter_expressions = []
                
                # Add regular filters as AND group
                if regular_filters:
                    filter_expressions.append(_build_and_group_filter(regular_filters))
                
                # Add NOT filters
                for not_filter in not_filters:
                    # Remove the 'not' key before building the filter
                    filter_without_not = {k: v for k, v in not_filter.items() if k != "not"}
                    filter_expressions.append(_build_not_filter(filter_without_not))
                
                # Combine all filters with AND
                if len(filter_expressions) == 1:
                    request_body["requests"][0]["dimensionFilter"] = filter_expressions[0]
                else:
                    request_body["requests"][0]["dimensionFilter"] = {
                        "andGroup": {
                            "expressions": filter_expressions
                        }
                    }
        
        # Add metric filters if provided
        if metric_filters or not_metric_filters:
            all_met_filters = []
            
            # Add regular metric filters
            if metric_filters:
                all_met_filters.extend(metric_filters)
            
            # Add negated metric filters
            if not_metric_filters:
                for not_filter in not_metric_filters:
                    all_met_filters.append({"not": True, **not_filter})
            
            if all_met_filters:
                # Separate regular and NOT filters
                regular_filters = [f for f in all_met_filters if not f.get("not", False)]
                not_filters = [f for f in all_met_filters if f.get("not", False)]
                
                filter_expressions = []
                
                # Add regular filters as AND group
                if regular_filters:
                    filter_expressions.append(_build_and_group_filter(regular_filters))
                
                # Add NOT filters
                for not_filter in not_filters:
                    # Remove the 'not' key before building the filter
                    filter_without_not = {k: v for k, v in not_filter.items() if k != "not"}
                    filter_expressions.append(_build_not_filter(filter_without_not))
                
                # Combine all filters with AND
                if len(filter_expressions) == 1:
                    request_body["requests"][0]["metricFilter"] = filter_expressions[0]
                else:
                    request_body["requests"][0]["metricFilter"] = {
                        "andGroup": {
                            "expressions": filter_expressions
                        }
                    }
        
        # Run the report
        response = await asyncio.to_thread(
            service.properties().batchRunReports(
                property=property_id,
                body=request_body
            ).execute
        )
        
        # Format and return results
        formatted_results = _format_report_results(response)
        
        return f"GA4 Report Results:\n{formatted_results}"
        
    except Exception as e:
        logger.error(f"[run_ga4_report] Error: {str(e)}")
        return f"Error running GA4 report: {str(e)}"


@server.tool()
@require_google_service("ga4_data", "ga4_read")
@handle_http_errors("get_ga4_realtime_report")
async def get_ga4_realtime_report(
    service,
    user_google_email: str,
    property_id: str,
    metrics: List[str] = Body(..., description="List of real-time metrics (e.g., ['activeUsers'])"),
    dimensions: List[str] = Body(default=[], description="List of dimensions for real-time data"),
    limit: int = Body(default=100, description="Maximum number of rows to return")
) -> str:
    """
    Retrieves real-time GA4 data.
    
    Args:
        user_google_email (str): The user's Google email address. Required.
        property_id (str): GA4 property ID (without 'properties/' prefix).
        metrics (List[str]): List of real-time metrics to retrieve.
        dimensions (List[str]): List of dimensions to group by.
        limit (int): Maximum number of rows to return.
        
    Returns:
        str: Formatted real-time report results.
    """
    logger.info(f"[get_ga4_realtime_report] Getting real-time data for property: {property_id}")
    
    try:
        # Format the property ID
        if not property_id.startswith('properties/'):
            property_id = f'properties/{property_id}'
        
        # Format metrics and dimensions
        formatted_metrics, formatted_dimensions = _format_metrics_and_dimensions(metrics, dimensions)
        
        # Build the request
        request_body = {
            "property": property_id,
            "metrics": formatted_metrics,
            "dimensions": formatted_dimensions,
            "limit": limit
        }
        
        # Run the real-time report
        response = await asyncio.to_thread(
            service.properties().runRealtimeReport(
                property=property_id,
                body=request_body
            ).execute
        )
        
        # Format results
        if not response:
            return "No real-time data available"
        
        result_lines = ["Real-time GA4 Data:", "=" * 25]
        
        # Get headers
        dimension_headers = response.get('dimensionHeaders', [])
        metric_headers = response.get('metricHeaders', [])
        
        headers = [dim.get('name') for dim in dimension_headers] + [met.get('name') for met in metric_headers]
        if headers:
            result_lines.append("Headers: " + " | ".join(headers))
            result_lines.append("-" * 40)
        
        # Get rows
        rows = response.get('rows', [])
        if not rows:
            result_lines.append("No real-time data available")
        else:
            for row in rows:
                row_values = []
                
                # Add dimension values
                dimension_values = row.get('dimensionValues', [])
                row_values.extend([dim.get('value', '') for dim in dimension_values])
                
                # Add metric values
                metric_values = row.get('metricValues', [])
                row_values.extend([met.get('value', '') for met in metric_values])
                
                if row_values:
                    result_lines.append(" | ".join(row_values))
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"[get_ga4_realtime_report] Error: {str(e)}")
        return f"Error retrieving real-time GA4 data: {str(e)}"


@server.tool()
@require_google_service("ga4_data", "ga4_read")
@handle_http_errors("get_ga4_metadata")
async def get_ga4_metadata(
    service,
    user_google_email: str,
    property_id: str
) -> str:
    """
    Retrieves metadata for a GA4 property including available metrics and dimensions.
    
    Args:
        user_google_email (str): The user's Google email address. Required.
        property_id (str): GA4 property ID (without 'properties/' prefix).
        
    Returns:
        str: Formatted metadata information.
    """
    logger.info(f"[get_ga4_metadata] Getting metadata for property: {property_id}")
    
    try:
        # Format the property ID
        if not property_id.startswith('properties/'):
            property_id = f'properties/{property_id}'
        
        # Get metadata
        metadata = await asyncio.to_thread(
            service.properties().getMetadata(name=f"{property_id}/metadata").execute
        )
        
        if not metadata:
            return "No metadata available for this property"
        
        result_lines = [
            f"GA4 Metadata for {property_id}:",
            "=" * 40
        ]
        
        # List metrics
        metrics = metadata.get('metrics', [])
        if metrics:
            result_lines.extend([
                "\nAvailable Metrics:",
                "-" * 20
            ])
            for metric in metrics:
                api_name = metric.get('apiName', 'Unknown')
                ui_name = metric.get('uiName', 'Unknown')
                description = metric.get('description', 'No description')
                result_lines.append(f"• {api_name} ({ui_name}): {description}")
        
        # List dimensions
        dimensions = metadata.get('dimensions', [])
        if dimensions:
            result_lines.extend([
                "\nAvailable Dimensions:",
                "-" * 22
            ])
            for dimension in dimensions:
                api_name = dimension.get('apiName', 'Unknown')
                ui_name = dimension.get('uiName', 'Unknown')
                description = dimension.get('description', 'No description')
                result_lines.append(f"• {api_name} ({ui_name}): {description}")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"[get_ga4_metadata] Error: {str(e)}")
        return f"Error retrieving GA4 metadata: {str(e)}"