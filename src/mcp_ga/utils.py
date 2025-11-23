"""Google Analytics MCP Server - Utility Functions

Utility functions for date handling, response formatting, and filter building.
References:
- DateRange: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/DateRange
- FilterExpression: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/FilterExpression
"""

import json
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


def get_date_range(days: int = 7) -> tuple[str, str]:
    """
    Calculate date range for queries following DateRange specification.
    
    Args:
        days: Number of days to go back from today
        
    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days - 1)
    
    return (
        start_date.strftime("%Y-%m-%d"),
        end_date.strftime("%Y-%m-%d")
    )


def validate_date(date_string: str) -> bool:
    """
    Validate date format per DateRange specification.
    
    Args:
        date_string: Date string to validate
        
    Returns:
        True if valid YYYY-MM-DD format, False otherwise
    """
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def format_report_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format Analytics Data API report response for better readability.
    
    Args:
        response: Raw API response from runReport
        
    Returns:
        Formatted response with structured data
    """
    formatted = {
        "rows": [],
        "row_count": response.get("rowCount", 0),
        "metadata": response.get("metadata", {}),
    }
    
    # Extract dimension headers
    dimension_headers = [
        header.get("name") for header in response.get("dimensionHeaders", [])
    ]
    
    # Extract metric headers
    metric_headers = [
        header.get("name") for header in response.get("metricHeaders", [])
    ]
    
    # Format rows
    for row in response.get("rows", []):
        formatted_row = {}
        
        # Add dimensions
        for i, value in enumerate(row.get("dimensionValues", [])):
            if i < len(dimension_headers):
                formatted_row[dimension_headers[i]] = value.get("value")
        
        # Add metrics
        for i, value in enumerate(row.get("metricValues", [])):
            if i < len(metric_headers):
                metric_value = value.get("value")
                # Try to convert to number if possible
                try:
                    metric_value = float(metric_value)
                    # Convert to int if it's a whole number
                    if metric_value.is_integer():
                        metric_value = int(metric_value)
                except (ValueError, AttributeError):
                    pass
                formatted_row[metric_headers[i]] = metric_value
        
        formatted["rows"].append(formatted_row)
    
    # Add totals if available
    if "totals" in response:
        formatted["totals"] = {}
        for i, value in enumerate(response["totals"][0].get("metricValues", [])):
            if i < len(metric_headers):
                metric_value = value.get("value")
                try:
                    metric_value = float(metric_value)
                    if metric_value.is_integer():
                        metric_value = int(metric_value)
                except (ValueError, AttributeError):
                    pass
                formatted["totals"][metric_headers[i]] = metric_value
    
    return formatted


def format_error_message(error: Exception) -> str:
    """
    Standardize error messages for consistent error handling.
    
    Args:
        error: Exception object
        
    Returns:
        Formatted error message string
    """
    error_msg = str(error)
    
    # Extract useful information from Google API errors
    if hasattr(error, 'resp'):
        status = getattr(error.resp, 'status', 'Unknown')
        error_msg = f"API Error {status}: {error_msg}"
    
    return error_msg


def encode_account_property_id(account_id: str = None, property_id: str = None) -> str:
    """
    URL encode account and/or property IDs for resource URIs.
    
    Args:
        account_id: Account ID (optional)
        property_id: Property ID (optional)
        
    Returns:
        URL-encoded string
    """
    parts = []
    if account_id:
        parts.append(urllib.parse.quote(account_id, safe=''))
    if property_id:
        parts.append(urllib.parse.quote(property_id, safe=''))
    return '/'.join(parts)


def decode_account_property_id(encoded_id: str) -> str:
    """
    URL decode account/property IDs from resource URIs.
    
    Args:
        encoded_id: URL-encoded ID string
        
    Returns:
        Decoded ID string
    """
    return urllib.parse.unquote(encoded_id)


def build_dimension_filter(
    dimension_name: str,
    values: List[str],
    match_type: str = "EXACT"
) -> Dict[str, Any]:
    """
    Helper for building FilterExpression for dimension filtering.
    Reference: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/FilterExpression
    
    Args:
        dimension_name: Name of the dimension to filter
        values: List of values to match
        match_type: Match type (EXACT, BEGINS_WITH, ENDS_WITH, CONTAINS, etc.)
        
    Returns:
        FilterExpression dictionary
    """
    if len(values) == 1:
        # Single value filter
        return {
            "filter": {
                "fieldName": dimension_name,
                "stringFilter": {
                    "matchType": match_type,
                    "value": values[0]
                }
            }
        }
    else:
        # Multiple values - use inListFilter
        return {
            "filter": {
                "fieldName": dimension_name,
                "inListFilter": {
                    "values": values
                }
            }
        }


def build_metric_aggregation(metrics: List[str]) -> List[Dict[str, str]]:
    """
    Helper for building metric aggregations.
    
    Args:
        metrics: List of metric names
        
    Returns:
        List of metric dictionaries
    """
    return [{"name": metric} for metric in metrics]


def parse_property_name(property_name: str) -> str:
    """
    Parse property name to extract property ID.
    Property names are in format: properties/{property_id}
    
    Args:
        property_name: Full property name from API
        
    Returns:
        Property ID
    """
    if property_name.startswith("properties/"):
        return property_name.split("/")[1]
    return property_name


def parse_account_name(account_name: str) -> str:
    """
    Parse account name to extract account ID.
    Account names are in format: accounts/{account_id}
    
    Args:
        account_name: Full account name from API
        
    Returns:
        Account ID
    """
    if account_name.startswith("accounts/"):
        return account_name.split("/")[1]
    return account_name
