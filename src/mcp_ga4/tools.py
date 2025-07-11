from mcp.server.fastmcp import Context
from mcp_ga4.auth import ga4_client, is_authenticated
from mcp_ga4.utils import print_report_response, _build_filter_expression
from typing import Optional, Dict, List, Union
from google.analytics.data_v1beta.types import (
    BatchRunReportsRequest,
    RunReportRequest,
    DateRange,
    Metric,
    Dimension,
    FilterExpression,
    Filter,
    FilterExpressionList,
    RunPivotReportRequest,
    Pivot,
    OrderBy
)
import asyncio
import inspect
import json
import os
from mcp_ga4.models import GA4ReportParams, GA4PivotReportParams
from mcp_ga4.utils import parse_property_id

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

def list_ga4_properties():
    """
    List all GA4 properties accessible by the authenticated user.
    
    Returns:
        List[Dict]: List of GA4 properties with their details
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
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

def get_metadata(property_id: str) -> Dict:
    """
    Get GA4 metadata for a specific property including dimensions and metrics.
    
    Args:
        property_id: The GA4 property ID (e.g., 'properties/123456789')
    
    Returns:
        Dict: Metadata including dimensions and metrics
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
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

def run_report(property_id: str, start_date: str, end_date: str, metrics: List[str], dimensions: List[str] = None) -> Dict:
    """
    Run a GA4 report.
    
    Args:
        property_id: The GA4 property ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        metrics: List of metrics to include
        dimensions: List of dimensions to include
    
    Returns:
        Dict: Report data
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Build request
        request = RunReportRequest(
            property=parsed_id,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric) for metric in metrics],
            dimensions=[Dimension(name=dimension) for dimension in (dimensions or [])]
        )
        
        # Run report
        response = data_client.run_report(request)
        
        # Format response
        return print_report_response(response)
        
    except Exception as e:
        raise ValueError(f"Error running report: {str(e)}")

def batch_run_reports(property_id: str, requests: List[Dict]) -> Dict:
    """
    Run multiple GA4 reports in a batch.
    
    Args:
        property_id: The GA4 property ID
        requests: List of report request dictionaries
    
    Returns:
        Dict: Batch report data
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Build batch request
        report_requests = []
        for req in requests:
            report_request = RunReportRequest(
                property=parsed_id,
                date_ranges=[DateRange(start_date=req['start_date'], end_date=req['end_date'])],
                metrics=[Metric(name=metric) for metric in req['metrics']],
                dimensions=[Dimension(name=dimension) for dimension in req.get('dimensions', [])]
            )
            report_requests.append(report_request)
        
        batch_request = BatchRunReportsRequest(
            property=parsed_id,
            requests=report_requests
        )
        
        # Run batch report
        response = data_client.batch_run_reports(batch_request)
        
        # Format response
        results = []
        for report in response.reports:
            results.append(print_report_response(report))
        
        return {
            'property_id': parsed_id,
            'reports': results,
            'report_count': len(results)
        }
        
    except Exception as e:
        raise ValueError(f"Error running batch reports: {str(e)}")

def run_pivot_report(property_id: str, start_date: str, end_date: str, metrics: List[str], dimensions: List[str], pivots: List[Dict]) -> Dict:
    """
    Run a GA4 pivot report.
    
    Args:
        property_id: The GA4 property ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        metrics: List of metrics to include
        dimensions: List of dimensions to include
        pivots: List of pivot configurations
    
    Returns:
        Dict: Pivot report data
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Build pivots
        pivot_objects = []
        for pivot in pivots:
            pivot_obj = Pivot(
                field_names=pivot['field_names'],
                limit=pivot.get('limit', 100),
                offset=pivot.get('offset', 0)
            )
            pivot_objects.append(pivot_obj)
        
        # Build request
        request = RunPivotReportRequest(
            property=parsed_id,
            date_ranges=[DateRange(start_date=start_date, end_date=end_date)],
            metrics=[Metric(name=metric) for metric in metrics],
            dimensions=[Dimension(name=dimension) for dimension in dimensions],
            pivots=pivot_objects
        )
        
        # Run pivot report
        response = data_client.run_pivot_report(request)
        
        # Format response (simplified)
        return {
            'property_id': parsed_id,
            'pivot_headers': [header.pivot_dimension_headers for header in response.pivot_headers],
            'dimension_headers': [header.name for header in response.dimension_headers],
            'metric_headers': [header.name for header in response.metric_headers],
            'row_count': response.row_count,
            'metadata': response.metadata
        }
        
    except Exception as e:
        raise ValueError(f"Error running pivot report: {str(e)}")

def batch_run_pivot_reports(property_id: str, requests: List[Dict]) -> Dict:
    """
    Run multiple GA4 pivot reports in a batch.
    
    Args:
        property_id: The GA4 property ID
        requests: List of pivot report request dictionaries
    
    Returns:
        Dict: Batch pivot report data
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Build batch request - simplified implementation
        results = []
        for req in requests:
            result = run_pivot_report(
                property_id=property_id,
                start_date=req['start_date'],
                end_date=req['end_date'],
                metrics=req['metrics'],
                dimensions=req['dimensions'],
                pivots=req['pivots']
            )
            results.append(result)
        
        return {
            'property_id': parsed_id,
            'pivot_reports': results,
            'report_count': len(results)
        }
        
    except Exception as e:
        raise ValueError(f"Error running batch pivot reports: {str(e)}")

def check_compatibility(property_id: str, dimensions: List[str] = None, metrics: List[str] = None) -> Dict:
    """
    Check if dimensions and metrics are compatible for GA4 reporting.
    
    Args:
        property_id: The GA4 property ID
        dimensions: List of dimensions to check
        metrics: List of metrics to check
    
    Returns:
        Dict: Compatibility information
    """
    client_id = get_client_id_from_env()
    
    # Check if user is authenticated
    if not is_authenticated(client_id):
        raise ValueError("User not authenticated. Please visit /authorize to authenticate first.")
    
    try:
        # Parse and validate property ID
        parsed_id = parse_property_id(property_id)
        
        # Get the data client
        data_client = ga4_client(client_id, type='data')
        
        # Get metadata to check compatibility
        metadata = data_client.get_metadata(name=f"{parsed_id}/metadata")
        
        # Check if requested dimensions and metrics exist
        available_dimensions = [dim.api_name for dim in metadata.dimensions]
        available_metrics = [met.api_name for met in metadata.metrics]
        
        compatibility = {
            'property_id': parsed_id,
            'dimensions': {
                'requested': dimensions or [],
                'available': available_dimensions,
                'valid': [],
                'invalid': []
            },
            'metrics': {
                'requested': metrics or [],
                'available': available_metrics,
                'valid': [],
                'invalid': []
            }
        }
        
        # Check dimensions
        for dim in (dimensions or []):
            if dim in available_dimensions:
                compatibility['dimensions']['valid'].append(dim)
            else:
                compatibility['dimensions']['invalid'].append(dim)
        
        # Check metrics
        for met in (metrics or []):
            if met in available_metrics:
                compatibility['metrics']['valid'].append(met)
            else:
                compatibility['metrics']['invalid'].append(met)
        
        return compatibility
        
    except Exception as e:
        raise ValueError(f"Error checking compatibility: {str(e)}")
    
    