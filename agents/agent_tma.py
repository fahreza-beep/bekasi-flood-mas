import re
from datetime import datetime
from state import FloodState

# Ambang Batas Normal Resmi BPBD Kota Bekasi & DBMSDA
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
    """
    Ekstrak angka TMA (cm) murni untuk 3 titik utama KP2C:
    Hulu Cileungsi, Hulu Cikeas, dan P2C.
    """
    latest_tma = {"cileungsi": 0, "cikeas": 0, "p2c": 0}
    if not text:
        return latest_tma

    text_lower = text.lower()

    # Pattern presisi mengambil angka setelah kata 'tma'
    patterns = {
        "cileungsi": r'cileungsi[^\n]*?tma\s*(\d+)',
        "cikeas": r'cikeas[^\n]*?tma\s*(\d+)',
        "p2c": r'(?:p2c|pertemuan)[^\n]*?tma\s*(\d+)'
    }

    for pos, pattern in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            latest_tma[pos] = int(match.group(1))

    return latest_tma


def agent_3_tma(state: FloodState) -> FloodState:
    print("\n[Agent 3] Membedah TMA Real-time Jam Terakhir & Logika Hidrologi BPBD...")
    
    # Handling field_reports tipe string maupun list
    field_reports_data = state.get("field_reports", "")
    if isinstance(field_reports_data, list):
        combined_report_text = "\n".join(field_reports_data)
    else:
        combined_report_text = str(field_reports_data) if field_reports_data else ""
    
    # Ekstrak angka TMA aktual dari laporan KP2C
    tma = parse_tma_from_text_or_ocr(combined_report_text)
    
    is_cileungsi_kritis = tma["cileungsi"] > BATAS_NORMAL_BPBD["cileungsi"]
    is_cikeas_kritis = tma["cikeas"] > BATAS_NORMAL_BPBD["cikeas"]
    is_p2c_kritis = tma["p2c"] > BATAS_NORMAL_BPBD["p2c"]

    if is_cileungsi_kritis:
        tma_status = f"SIAGA/WASPADA HULU CILEUNGSI (TMA Terbaca: Cileungsi {tma['cileungsi']}cm, Cikeas {tma['cikeas']}cm, P2C {tma['p2c']}cm)"
        travel_time = 4.0
    elif is_cikeas_kritis:
        tma_status = f"SIAGA/WASPADA HULU CIKEAS (TMA Terbaca: Cileungsi {tma['cileungsi']}cm, Cikeas {tma['cikeas']}cm, P2C {tma['p2c']}cm)"
        travel_time = 3.0
    elif is_p2c_kritis:
        tma_status = f"SIAGA/WASPADA P2C (TMA Terbaca: Cileungsi {tma['cileungsi']}cm, Cikeas {tma['cikeas']}cm, P2C {tma['p2c']}cm)"
        travel_time = 1.0
    else:
        tma_status = f"NORMAL BPBD (TMA Terbaca: Cileungsi {tma['cileungsi']}cm, Cikeas {tma['cikeas']}cm, P2C {tma['p2c']}cm)"
        travel_time = 0.0

    # Pertahankan audit log dari agen-agen sebelumnya
    raw_audit_logs = state.get("raw_audit_logs", {})
    
    # Isi log audit Agent 3 lengkap dengan key "raw_data"
    raw_audit_logs["agent_3_hydrology"] = {
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
        "travel_time_hours": travel_time,
        "raw_audit_logs": raw_audit_logs
    }
