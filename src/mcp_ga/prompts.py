"""Google Analytics MCP Server - Prompts Module

This module implements MCP prompts for common analytics analysis tasks.
"""


async def analyze_traffic(
    property_id: str,
    time_period: str = "last 30 days"
) -> str:
    """
    Generate a prompt for analyzing traffic patterns.
    
    Args:
        property_id: GA4 property ID to analyze
        time_period: Time period description
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the traffic for Google Analytics property {property_id} over {time_period}.

Please provide a comprehensive traffic analysis including:

1. **Overall Performance**
   - Total active users, sessions, and page views
   - Trends and patterns in the data
   - Key performance indicators

2. **Traffic Sources**
   - Top traffic sources and mediums
   - Source/medium combinations driving the most traffic
   - Quality of traffic from each source

3. **User Behavior**
   - Top performing pages
   - Average session duration and bounce rate
   - User engagement patterns

4. **Geographic Insights**
   - Top countries and regions
   - Geographic distribution of traffic

5. **Device Analysis**
   - Desktop vs mobile vs tablet usage
   - Device-specific performance metrics

6. **Recommendations**
   - Opportunities for improvement
   - Areas of concern
   - Actionable insights

Use the available tools to gather the necessary data and provide a detailed analysis."""


async def conversion_analysis(
    property_id: str,
    conversion_event: str = "purchase"
) -> str:
    """
    Generate a prompt for conversion funnel analysis.
    
    Args:
        property_id: GA4 property ID to analyze
        conversion_event: Name of the conversion event to analyze
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the conversion funnel for the '{conversion_event}' event in Google Analytics property {property_id}.

Please provide a detailed conversion analysis including:

1. **Conversion Overview**
   - Total conversions and conversion rate
   - Trends over time
   - Comparison to previous periods

2. **Funnel Analysis**
   - Key steps in the conversion path
   - Drop-off points and bottlenecks
   - Pages with highest conversion rates

3. **Traffic Source Performance**
   - Which sources drive the most conversions
   - Conversion rates by source/medium
   - ROI by traffic source

4. **User Segments**
   - New vs returning user conversion rates
   - Geographic conversion patterns
   - Device-specific conversion rates

5. **Page Performance**
   - Landing pages with best conversion rates
   - Pages that assist in conversions
   - Pages where users drop off

6. **Optimization Opportunities**
   - Quick wins for improving conversion rate
   - A/B test recommendations
   - User experience improvements

Use the run_report tool with appropriate dimensions and metrics to gather conversion data."""


async def audience_insights(
    property_id: str,
    time_period: str = "last 30 days"
) -> str:
    """
    Generate a prompt for audience demographics and behavior analysis.
    
    Args:
        property_id: GA4 property ID to analyze
        time_period: Time period description
        
    Returns:
        Formatted prompt string
    """
    return f"""Analyze the audience for Google Analytics property {property_id} over {time_period}.

Please provide comprehensive audience insights including:

1. **Demographic Overview**
   - Age distribution
   - Gender breakdown
   - Geographic distribution

2. **User Behavior**
   - New vs returning users
   - User engagement levels
   - Session frequency and recency

3. **Interest Categories**
   - Affinity categories
   - In-market segments
   - User interests

4. **Technology**
   - Browser usage
   - Operating systems
   - Device categories and models
   - Screen resolutions

5. **Engagement Metrics**
   - Average session duration by segment
   - Pages per session
   - Bounce rates by segment

6. **User Journey**
   - Common entry pages
   - Navigation patterns
   - Exit pages

7. **Audience Recommendations**
   - Target audience opportunities
   - Personalization strategies
   - Content recommendations for different segments

Use the available dimensions like userAgeBracket, userGender, country, deviceCategory, and relevant metrics to build a complete audience profile."""


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
        
    Returns:
        Formatted prompt string
    """
    return f"""Compare the performance of Google Analytics property {property_id} between {period1} and {period2}.

Please provide a detailed period-over-period comparison including:

1. **Overall Performance Comparison**
   - Active users: change and percentage difference
   - Sessions: change and percentage difference
   - Page views: change and percentage difference
   - Engagement rate: change and percentage difference

2. **Traffic Source Changes**
   - Which sources increased or decreased
   - New traffic sources that appeared
   - Sources that disappeared or declined significantly

3. **Content Performance**
   - Pages that gained or lost traffic
   - New top-performing pages
   - Pages with declining performance

4. **User Behavior Changes**
   - Changes in average session duration
   - Bounce rate variations
   - Engagement metric changes

5. **Geographic Shifts**
   - Countries with significant changes
   - Emerging markets
   - Declining regions

6. **Device Trends**
   - Shifts in device usage
   - Platform-specific changes

7. **Key Insights**
   - Most significant changes (positive and negative)
   - Potential causes for major shifts
   - Trends to monitor

8. **Action Items**
   - Opportunities to capitalize on positive trends
   - Issues requiring immediate attention
   - Strategic recommendations

For each comparison, calculate the absolute change and percentage change. Highlight changes greater than 20% as significant."""
