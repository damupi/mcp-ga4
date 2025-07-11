import re
from typing import List, Union
from google.analytics.data_v1beta.types import FilterExpression, Filter, FilterExpressionList

def print_report_response(response):
    """
    Prints the report response in a readable format.

    Args:
        response (RunReportResponse): The response from the run_report method.
    """
    for row in response.rows:
        session_medium = row.dimension_values[0].value
        sessions = row.metric_values[0].value
        print(f"Session Medium: {session_medium}, Sessions: {sessions}")

def parse_property_id(property_id: str) -> str:
    """
    Parse the property_id to get only number and format it with properties/ prefix.
    
    Args:
        property_id (str): The GA4 property ID (e.g., '267108084' or 'properties/267108084')
    
    Returns:
        str: Formatted property ID with 'properties/' prefix
        
    Raises:
        ValueError: If the property_id doesn't contain any numbers
    """
    if not property_id:
        raise ValueError("Property ID cannot be empty")
        
    # extract only number from property_id
    match = re.search(r'\d+', property_id)
    if not match:
        raise ValueError(f"Invalid property ID format: {property_id}. Must contain at least one number.")
        
    numeric_id = match.group()
    # Add properties/ prefix
    return f"properties/{numeric_id}"

# --- Filter Expression Utilities ---
def _build_single_filter(condition: dict) -> FilterExpression:
    """Handles individual filter conditions
    Args:
        condition: A dictionary containing:
            - field: The field name to filter on
            - value: The value to filter with
            - operator: One of:
                For strings: "EXACT", "BEGINS_WITH", "ENDS_WITH", "CONTAINS", "FULL_REGEXP", "PARTIAL_REGEXP"
                For numbers: "EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL", "GREATER_THAN", "GREATER_THAN_OR_EQUAL"
            - case_sensitive: (optional) boolean for string filters
    """
    string_operator_map = {
        "=": "EXACT",
        "!=": "NOT_EXACT",
        "contains": "CONTAINS",
        "starts_with": "BEGINS_WITH",
        "ends_with": "ENDS_WITH",
        "regex": "FULL_REGEXP",
        "partial_regex": "PARTIAL_REGEXP",
        # Direct API values
        "EXACT": "EXACT",
        "NOT_EXACT": "NOT_EXACT",
        "BEGINS_WITH": "BEGINS_WITH",
        "ENDS_WITH": "ENDS_WITH",
        "CONTAINS": "CONTAINS",
        "FULL_REGEXP": "FULL_REGEXP",
        "PARTIAL_REGEXP": "PARTIAL_REGEXP"
    }
    numeric_operator_map = {
        "=": "EQUAL",
        "!=": "NOT_EQUAL",
        ">": "GREATER_THAN",
        ">=": "GREATER_THAN_OR_EQUAL",
        "<": "LESS_THAN",
        "<=": "LESS_THAN_OR_EQUAL",
        # Direct API values
        "EQUAL": "EQUAL",
        "NOT_EQUAL": "NOT_EQUAL",
        "GREATER_THAN": "GREATER_THAN",
        "GREATER_THAN_OR_EQUAL": "GREATER_THAN_OR_EQUAL",
        "LESS_THAN": "LESS_THAN",
        "LESS_THAN_OR_EQUAL": "LESS_THAN_OR_EQUAL"
    }
    operator = condition["operator"]
    field_name = condition["field"]
    value = condition["value"]
    if operator in string_operator_map:
        match_type = string_operator_map[operator]
        if match_type not in ["EXACT", "NOT_EXACT", "BEGINS_WITH", "ENDS_WITH", "CONTAINS", "FULL_REGEXP", "PARTIAL_REGEXP"]:
            raise ValueError(f"Invalid string operator: {operator}. Valid operators are: {', '.join(string_operator_map.keys())}")
        return FilterExpression(
            filter=Filter(
                field_name=field_name,
                string_filter=Filter.StringFilter(
                    match_type=match_type,
                    value=str(value),
                    case_sensitive=condition.get("case_sensitive", False)
                )
            )
        )
    elif operator in numeric_operator_map:
        operation = numeric_operator_map[operator]
        if operation not in ["EQUAL", "NOT_EQUAL", "GREATER_THAN", "GREATER_THAN_OR_EQUAL", "LESS_THAN", "LESS_THAN_OR_EQUAL"]:
            raise ValueError(f"Invalid numeric operator: {operator}. Valid operators are: {', '.join(numeric_operator_map.keys())}")
        try:
            numeric_value = float(value)
        except ValueError:
            raise ValueError(f"Invalid numeric value: {value}")
        return FilterExpression(
            filter=Filter(
                field_name=field_name,
                numeric_filter=Filter.NumericFilter(
                    operation=operation,
                    value=numeric_value
                )
            )
        )
    else:
        raise ValueError(f"Invalid operator: {operator}. Must be one of: {', '.join(list(string_operator_map.keys()) + list(numeric_operator_map.keys()))}")

def _build_filter_expression(filters: List[Union[dict, List[dict]]]) -> FilterExpression:
    """Converts human-friendly filters to GA4's FilterExpression"""
    expressions = []
    for f in filters:
        if isinstance(f, dict) and "AND" in f:
            and_group = FilterExpressionList(
                expressions=[_build_single_filter(cond) for cond in f["AND"]]
            )
            expressions.append(FilterExpression(and_group=and_group))
        elif isinstance(f, dict) and "OR" in f:
            or_group = FilterExpressionList(
                expressions=[_build_single_filter(cond) for cond in f["OR"]]
            )
            expressions.append(FilterExpression(or_group=or_group))
        else:
            expressions.append(_build_single_filter(f))
    return FilterExpression(and_group=FilterExpressionList(expressions=expressions))
