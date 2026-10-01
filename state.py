from typing import TypedDict, Optional, Dict, Any, Annotated

def merge_audit_logs(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    merged = dict(left or {})
    if right:
        merged.update(right)
    return merged

class FloodState(TypedDict):
    hulu_forecast: Optional[str]
    field_reports: Optional[Any]
    raw_social_data: Optional[Dict[str, Any]]
    tma_status: Optional[str]
    parsed_tma: Optional[Dict[str, int]]
    travel_time_hours: Optional[float]
    flood_risk_level: Optional[str]
    warning_statement: Optional[str]
    raw_audit_logs: Annotated[Optional[Dict[str, Any]], merge_audit_logs]
