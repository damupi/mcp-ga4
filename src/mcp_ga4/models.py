from pydantic import BaseModel, Field
from typing import List, Optional, Union, Dict
from mcp.server.fastmcp.utilities.func_metadata import ArgModelBase

class GA4ReportParams(ArgModelBase):
    property_id: str = Field(
        ...,
        description=(
            "The GA4 property resource string. "
            "Must be in the format 'properties/{property_id}', e.g., 'properties/285857835'. "
            "See: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runReport"
        ),
        example="properties/285857835"
    )
    start_date: str = Field(..., description="Start date for the report in YYYY-MM-DD format.", example="2024-01-01")
    end_date: str = Field(..., description="End date for the report in YYYY-MM-DD format.", example="2024-01-31")
    metrics: List[str] = Field(..., description="List of metric names to include in the report.", example=["sessions"])
    dimensions: Optional[List[str]] = Field(None, description="List of dimension names to include in the report.", example=["country"])
    dimension_filters: Optional[List[Union[dict, List[dict]]]] = Field(
        None,
        description="List of filter conditions or nested groups for dimensions.",
        example=[
            {"field": "country", "value": "Japan", "operator": "="},
            {"AND": [
                {"field": "country", "value": "Japan", "operator": "="},
                {"field": "deviceCategory", "value": "Mobile", "operator": "="}
            ]}
        ]
    )
    limit: Optional[int] = Field(10, description="Maximum number of rows to return.", example=10)

class GA4PivotReportParams(ArgModelBase):
    property_id: str = Field(
        ...,
        description=(
            "The GA4 property resource string. "
            "Must be in the format 'properties/{property_id}', e.g., 'properties/285857835'. "
            "See: https://developers.google.com/analytics/devguides/reporting/data/v1/rest/v1beta/properties/runPivotReport"
        ),
        example="properties/285857835"
    )
    start_date: str = Field(..., description="Start date for the report in YYYY-MM-DD format.", example="2024-01-01")
    end_date: str = Field(..., description="End date for the report in YYYY-MM-DD format.", example="2024-01-31")
    metrics: List[str] = Field(..., description="List of metric names to include in the report.", example=["sessions"])
    dimensions: Optional[List[str]] = Field(None, description="List of dimension names to include in the report.", example=["country"])
    pivots: List[Dict] = Field(
        ...,
        description="List of pivot configurations. Each pivot must specify fieldNames and metrics.",
        example=[
            {
                "fieldNames": ["country"],
                "metrics": ["sessions", "users"],
                "limit": 10,
                "orderBys": [{"metricName": "sessions", "orderType": "DESCENDING"}]
            }
        ]
    )
    dimension_filters: Optional[List[Union[dict, List[dict]]]] = Field(
        None,
        description="List of filter conditions or nested groups for dimensions.",
        example=[
            {"field": "country", "value": "Japan", "operator": "="},
            {"AND": [
                {"field": "country", "value": "Japan", "operator": "="},
                {"field": "deviceCategory", "value": "Mobile", "operator": "="}
            ]}
        ]
    )
    metric_filters: Optional[List[Union[dict, List[dict]]]] = Field(
        None,
        description="List of filter conditions or nested groups for metrics.",
        example=[
            {"field": "sessions", "value": 100, "operator": ">"},
            {"AND": [
                {"field": "sessions", "value": 100, "operator": ">"},
                {"field": "users", "value": 50, "operator": ">"}
            ]}
        ]
    )
    limit: Optional[int] = Field(10, description="Maximum number of rows to return.", example=10)
    keep_empty_rows: Optional[bool] = Field(False, description="If true, rows with all metrics equal to 0 will be returned.")
    currency_code: Optional[str] = Field(None, description="A currency code in ISO4217 format, such as 'AED', 'USD', 'JPY'.")
