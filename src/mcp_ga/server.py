"""Google Analytics MCP Server - Main Server Module

A Model Context Protocol server providing LLMs with access to Google Analytics 4 data.
Built with FastMCP: https://fastmcp.wiki
"""

from fastmcp import FastMCP, Context

from mcp_ga import prompts, resources, tools

# Create FastMCP server instance
# Authentication is automatically configured from environment variables:
# - FASTMCP_SERVER_AUTH=fastmcp.server.auth.providers.google.GoogleProvider
# - FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=your-client-id
# - FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=your-secret
# - FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES=openid,email,analytics.readonly
mcp = FastMCP(
    name="Google Analytics MCP Server",
    version="0.1.0"
)



# ============================================================================
# CUSTOM ROUTES - Additional HTTP endpoints
# ============================================================================

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for monitoring and load balancers."""
    from starlette.responses import JSONResponse
    return JSONResponse({
        "status": "healthy",
        "server": "Google Analytics MCP",
        "version": "0.1.0"
    })


# ============================================================================
# TOOLS - Actions that LLMs can perform
# ============================================================================

@mcp.tool()
async def run_report(
    property_id: str,
    start_date: str,
    end_date: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
    dimension_filter: dict | None = None,
    limit: int = 10,
    offset: int = 0,
    ctx: Context = None,
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
        limit: Maximum number of rows to return
        offset: Number of rows to skip
        
    Returns:
        JSON string with formatted report data
    """
    return await tools.run_report(
        property_id, start_date, end_date, dimensions, metrics,
        dimension_filter, limit, offset, ctx
    )


@mcp.tool()
async def run_realtime_report(
    property_id: str,
    dimensions: list[str] | None = None,
    metrics: list[str] | None = None,
    limit: int = 10,
) -> str:
    """
    Get real-time analytics data (last 30 minutes).
    
    Args:
        property_id: GA4 property ID
        dimensions: List of dimension names
        metrics: List of metric names
        limit: Maximum number of rows to return
        
    Returns:
        JSON string with real-time data
    """
    return await tools.run_realtime_report(property_id, dimensions, metrics, limit)


@mcp.tool()
async def list_dimensions(property_id: str) -> str:
    """
    Get available dimensions with descriptions.
    
    Args:
        property_id: GA4 property ID
        
    Returns:
        JSON string with list of dimensions
    """
    return await tools.list_dimensions(property_id)


@mcp.tool()
async def list_metrics(property_id: str) -> str:
    """
    Get available metrics with descriptions.
    
    Args:
        property_id: GA4 property ID
        
    Returns:
        JSON string with list of metrics
    """
    return await tools.list_metrics(property_id)


@mcp.tool()
async def list_accounts(ctx: Context = None) -> str:
    """
    List all GA4 accounts accessible to the user.
    
    Returns:
        JSON string with list of accounts
    """
    return await tools.list_accounts(ctx)


@mcp.tool()
async def list_properties(account_id: str) -> str:
    """
    List all GA4 properties for an account.
    
    Args:
        account_id: Account ID
        
    Returns:
        JSON string with list of properties
    """
    return await tools.list_properties(account_id)


@mcp.tool()
async def get_property(property_id: str) -> str:
    """
    Get property details.
    
    Args:
        property_id: Property ID
        
    Returns:
        JSON string with property details
    """
    return await tools.get_property(property_id)


@mcp.tool()
async def list_data_streams(property_id: str) -> str:
    """
    List data streams for a property.
    
    Args:
        property_id: Property ID
        
    Returns:
        JSON string with list of data streams
    """
    return await tools.list_data_streams(property_id)


@mcp.tool()
async def get_data_stream(property_id: str, stream_id: str) -> str:
    """
    Get data stream details.
    
    Args:
        property_id: Property ID
        stream_id: Data stream ID
        
    Returns:
        JSON string with data stream details
    """
    return await tools.get_data_stream(property_id, stream_id)


# ============================================================================
# RESOURCES - Read-only data sources
# ============================================================================

@mcp.resource("ga://accounts")
async def get_accounts_resource(ctx: Context) -> str:
    """List all GA4 accounts accessible to the user."""
    return await resources.get_accounts_list(ctx)


@mcp.resource("ga://accounts/{account_id}/properties")
async def get_account_properties_resource(account_id: str) -> str:
    """List all properties for a specific account."""
    return await resources.get_account_properties(account_id)


@mcp.resource("ga://config")
async def get_config_resource() -> str:
    """Get server configuration and status."""
    return await resources.get_config()


@mcp.resource("ga://accounts/{account_id}/properties/{property_id}/summary")
async def get_analytics_summary_resource(account_id: str, property_id: str) -> str:
    """Get recent analytics summary for a property (last 28 days)."""
    return await resources.get_analytics_summary(account_id, property_id)


@mcp.resource("ga://accounts/{account_id}/properties/{property_id}/top-pages")
async def get_top_pages_resource(account_id: str, property_id: str) -> str:
    """Get top 10 pages for a property (last 7 days)."""
    return await resources.get_top_pages(account_id, property_id)


@mcp.resource("ga://accounts/{account_id}/properties/{property_id}/top-sources")
async def get_top_sources_resource(account_id: str, property_id: str) -> str:
    """Get top 10 traffic sources for a property (last 7 days)."""
    return await resources.get_top_sources(account_id, property_id)


@mcp.resource("ga://accounts/{account_id}/properties/{property_id}/realtime")
async def get_realtime_resource(account_id: str, property_id: str) -> str:
    """Get real-time analytics data for a property."""
    return await resources.get_realtime_data(account_id, property_id)


# ============================================================================
# PROMPTS - Reusable templates for LLM interactions
# ============================================================================

@mcp.prompt()
async def analyze_traffic(
    property_id: str,
    time_period: str = "last 30 days"
) -> str:
    """
    Generate a prompt for analyzing traffic patterns.
    
    Args:
        property_id: GA4 property ID to analyze
        time_period: Time period description
    """
    return await prompts.analyze_traffic(property_id, time_period)


@mcp.prompt()
async def conversion_analysis(
    property_id: str,
    conversion_event: str = "purchase"
) -> str:
    """
    Generate a prompt for conversion funnel analysis.
    
    Args:
        property_id: GA4 property ID to analyze
        conversion_event: Name of the conversion event to analyze
    """
    return await prompts.conversion_analysis(property_id, conversion_event)


@mcp.prompt()
async def audience_insights(
    property_id: str,
    time_period: str = "last 30 days"
) -> str:
    """
    Generate a prompt for audience demographics and behavior analysis.
    
    Args:
        property_id: GA4 property ID to analyze
        time_period: Time period description
    """
    return await prompts.audience_insights(property_id, time_period)


@mcp.prompt()
async def compare_periods(
    property_id: str,
    period1: str = "last 7 days",
    period2: str = "previous 7 days"
) -> str:
    """
    Generate a prompt for period-over-period comparison.
    
    Args:
        property_id: GA4 property ID to analyze
        period1: First time period description
        period2: Second time period description
    """
    return await prompts.compare_periods(property_id, period1, period2)
