import operator
from typing import TypedDict, Optional, List, Dict, Any, Annotated

def merge_audit_logs(left: Optional[Dict[str, Any]], right: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Fungsi reducer untuk menggabungkan dictionary audit log dari beberapa agent yang berjalan paralel.
    """
    merged = dict(left or {})
    if right:
        merged.update(right)
    return merged

class FloodState(TypedDict):
    # Context Path Utama
    hulu_forecast: Optional[str]
    field_reports: Optional[List[str]]
    tma_status: Optional[str]
    travel_time_hours: Optional[float]
    flood_risk_level: Optional[str]
    warning_statement: Optional[str]
    
    # Audit Trail (Gunakan Annotated + Reducer agar aman untuk eksekusi paralel)
    raw_audit_logs: Annotated[Optional[Dict[str, Any]], merge_audit_logs]
