from mcp.server.fastmcp import Context
from typing import List, Dict, Optional
from mcp_ga4.auth import ga4_client, is_authenticated
from mcp_ga4.utils import parse_property_id
import asyncio
import os

def get_client_id_from_env() -> str:
    """
    Get client ID from environment variables.
    
    Returns:
        str: Client ID for OAuth authentication
    """
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        raise ValueError("GOOGLE_CLIENT_ID environment variable must be set for OAuth authentication")
    return client_id.strip('"\'')

def list_ga4_properties() -> List[Dict]:
    """
    Get a list of all GA4 properties objects accessible by the authenticated user
    
    Returns:
        List[Dict]: List of GA4 properties with their details
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError(f"User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Get the admin client
        admin_client = ga4_client(client_id, type='admin')
        
        # List all accounts first
        accounts = admin_client.list_accounts()
        
        properties = []
        for account in accounts:
            # For each account, list its properties
            account_name = account.name
            account_display_name = account.display_name
            
            # List properties for this account
            request = admin_client.list_properties(parent=account_name)
            
            for property in request:
                property_dict = {
                    'property_id': property.name,
                    'display_name': property.display_name,
                    'create_time': property.create_time.isoformat() if property.create_time else None,
                    'update_time': property.update_time.isoformat() if property.update_time else None,
                    'account_name': account_name,
                    'account_display_name': account_display_name,
                    'currency_code': property.currency_code,
                    'time_zone': property.time_zone,
                    'property_type': property.property_type.name if property.property_type else None,
                    'industry_category': property.industry_category.name if property.industry_category else None,
                    'service_level': property.service_level.name if property.service_level else None,
                }
                properties.append(property_dict)
        
        return properties
        
    except Exception as e:
        raise ValueError(f"Error listing GA4 properties: {str(e)}")

def get_ga4_property_details(property_id: str) -> Dict:
    """
    Get detailed information about a specific GA4 property
    
    Args:
        property_id: The GA4 property ID (e.g., 'properties/123456789')
    
    Returns:
        Dict: Detailed property information
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError(f"User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the admin client
        admin_client = ga4_client(client_id, type='admin')
        
        # Get property details
        property_details = admin_client.get_property(name=parsed_id)
        
        return {
            'property_id': property_details.name,
            'display_name': property_details.display_name,
            'create_time': property_details.create_time.isoformat() if property_details.create_time else None,
            'update_time': property_details.update_time.isoformat() if property_details.update_time else None,
            'currency_code': property_details.currency_code,
            'time_zone': property_details.time_zone,
            'property_type': property_details.property_type.name if property_details.property_type else None,
            'industry_category': property_details.industry_category.name if property_details.industry_category else None,
            'service_level': property_details.service_level.name if property_details.service_level else None,
            'parent': property_details.parent,
        }
        
    except Exception as e:
        raise ValueError(f"Error getting property details: {str(e)}")

def get_ga4_metadata(property_id: str) -> Dict:
    """
    Get GA4 metadata for a specific property including dimensions and metrics
    
    Args:
        property_id: The GA4 property ID (e.g., 'properties/123456789')
    
    Returns:
        Dict: Metadata including dimensions and metrics
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError(f"User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Get metadata
        metadata = data_client.get_metadata(name=f"{parsed_id}/metadata")
        
        # Extract dimensions and metrics
        dimensions = []
        metrics = []
        
        for dimension in metadata.dimensions:
            dimensions.append({
                'api_name': dimension.api_name,
                'ui_name': dimension.ui_name,
                'description': dimension.description,
                'custom_definition': dimension.custom_definition,
                'deprecated_api_names': list(dimension.deprecated_api_names) if dimension.deprecated_api_names else []
            })
        
        for metric in metadata.metrics:
            metrics.append({
                'api_name': metric.api_name,
                'ui_name': metric.ui_name,
                'description': metric.description,
                'type': metric.type.name if metric.type else None,
                'expression': metric.expression,
                'custom_definition': metric.custom_definition,
                'deprecated_api_names': list(metric.deprecated_api_names) if metric.deprecated_api_names else []
            })
        
        return {
            'property_id': parsed_id,
            'dimensions': dimensions,
            'metrics': metrics,
            'dimension_count': len(dimensions),
            'metric_count': len(metrics)
        }
        
    except Exception as e:
        raise ValueError(f"Error getting metadata: {str(e)}")

def get_ga4_term_mappings(term: str) -> dict:
    """
    Maps natural language terms to GA4 API parameters.
    Example: "exit clicks" → {"dimension": "eventName", "value": "exit_click_goal"}
    """
    term_mappings = {
        "exit%20clicks": {
            "metadata": "dimension",
            "name": "eventName",
            "value": "exit_click_goal",
            "operator": "="
        },
        "pageviews": {
            "metadata": "metric",
            "name": "screenPageViews",
            "value": "screenPageViews",
            "operator": "="
        },
        "mobile users": {
            "metadata": "dimension",
            "name": "deviceCategory",
            "value": "mobile",
            "operator": "="
        }
    }
    return term_mappings.get(term.lower(), {})
