import re
from datetime import datetime
from state import FloodState

BATAS_NORMAL_BPBD = {
    "cileungsi": 100,
    "cikeas": 200,
    "p2c": 350
}

TRAVEL_TIME_RULES = {
    "cileungsi_to_p2c": "3 - 4 Jam",
    "cikeas_to_p2c": "2 - 3 Jam",
    "p2c_to_bekasi": "1 - 1.5 Jam"
}

def parse_tma_from_text_or_ocr(text: str) -> dict:
    latest_tma = {"cileungsi": 0, "cikeas": 0, "p2c": 0}
    if not text:
        return latest_tma

    clean_text = text.replace('\xa0', ' ')

    def extract_tma(section_match):
        if not section_match:
            return 0
        sec_str = section_match.group(1)
        matches = re.findall(r'tma\s*(\d+)', sec_str, re.IGNORECASE)
        return int(matches[-1]) if matches else 0

    cileungsi_sec = re.search(r'\*?Hulu Cileungsi\*?[\s\S]*?\*?BATAS NORMAL.*?\n([\s\S]*?)(?=\*?Hulu Cikeas\*?|\Z)', clean_text, re.IGNORECASE)
    cikeas_sec = re.search(r'\*?Hulu Cikeas\*?[\s\S]*?\*?BATAS NORMAL.*?\n([\s\S]*?)(?=\*?Pertemuan|\*?P2C\*?|\Z)', clean_text, re.IGNORECASE)
    p2c_sec = re.search(r'\*?(?:Pertemuan Cileungsi\s*-\s*Cikeas|P2C)\*?[\s\S]*?\*?BATAS NORMAL.*?\n([\s\S]*?)(?=\(Jika|Ket:|\Z)', clean_text, re.IGNORECASE)

    latest_tma["cileungsi"] = extract_tma(cileungsi_sec)
    latest_tma["cikeas"] = extract_tma(cikeas_sec)
    latest_tma["p2c"] = extract_tma(p2c_sec)

    return latest_tma

def agent_3_tma(state: FloodState) -> FloodState:
    print("\n[Agent 3] Membedah TMA Real-time Jam Terakhir & Logika Hidrologi BPBD...")
    
    raw_social = state.get("raw_social_data", {})
    field_reports_data = state.get("field_reports", "")
    combined_report_text = ""

    if isinstance(raw_social, dict) and "data" in raw_social:
        combined_report_text = raw_social["data"].get("text", "")
    elif isinstance(raw_social, str) and raw_social.strip():
        combined_report_text = raw_social
    elif field_reports_data:
        if isinstance(field_reports_data, list):
            combined_report_text = "\n".join([str(x) for x in field_reports_data if x])
        else:
            combined_report_text = str(field_reports_data)

    tma = parse_tma_from_text_or_ocr(combined_report_text)
    
    is_cileungsi_kritis = tma["cileungsi"] > BATAS_NORMAL_BPBD["cileungsi"]
    is_cikeas_kritis = tma["cikeas"] > BATAS_NORMAL_BPBD["cikeas"]
    is_p2c_kritis = tma["p2c"] > BATAS_NORMAL_BPBD["p2c"]

    tma_detail_str = f"Cileungsi: {tma['cileungsi']} cm, Cikeas: {tma['cikeas']} cm, P2C: {tma['p2c']} cm"

    if is_cileungsi_kritis:
        tma_status = f"SIAGA/WASPADA HULU CILEUNGSI ({tma_detail_str})"
        travel_time = 4.0
    elif is_cikeas_kritis:
        tma_status = f"SIAGA/WASPADA HULU CIKEAS ({tma_detail_str})"
        travel_time = 3.0
    elif is_p2c_kritis:
        tma_status = f"SIAGA/WASPADA P2C ({tma_detail_str})"
        travel_time = 1.0
    else:
        tma_status = f"NORMAL BPBD ({tma_detail_str})"
        travel_time = 0.0

    raw_audit_logs = state.get("raw_audit_logs") or {}
    raw_audit_logs["agent_3_tma"] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "Hasil Ekstraksi Parsing Laporan Live KP2C (Agent 2)",
        "raw_data": {
            "parsed_tma_cm": tma,
            "official_bpbd_baselines": BATAS_NORMAL_BPBD,
            "official_travel_time_reference": TRAVEL_TIME_RULES
        }
    }

    return {
        "tma_status": tma_status,
        "parsed_tma": tma,
        "travel_time_hours": travel_time,
        "raw_audit_logs": raw_audit_logs
    }
