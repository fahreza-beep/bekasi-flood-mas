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
    Ekstrak angka TMA (cm) jam TERAKHIR untuk 3 titik utama KP2C:
    Hulu Cileungsi, Hulu Cikeas, dan P2C.
    """
    latest_tma = {"cileungsi": 0, "cikeas": 0, "p2c": 0}
    if not text:
        return latest_tma

    def get_last_tma_number(section_str: str) -> int:
        # Mencari semua pola angka setelah 'tma' (contoh: 'tma 25', 'tma 60')
        matches = re.findall(r'tma\s*(\d+)', section_str, re.IGNORECASE)
        if matches:
            return int(matches[-1]) # Ambil angka di baris jam paling bawah/terbaru
        return 0

    text_lower = text.lower()

    # 1. Seksi Hulu Cileungsi
    cileungsi_match = re.search(r'hulu cileungsi\s*\n(.*?)(?=hulu cikeas|\Z)', text_lower, re.DOTALL)
    if cileungsi_match:
        latest_tma["cileungsi"] = get_last_tma_number(cileungsi_match.group(1))

    # 2. Seksi Hulu Cikeas
    cikeas_match = re.search(r'hulu cikeas\s*\n(.*?)(?=pertemuan|p2c\b|\Z)', text_lower, re.DOTALL)
    if cikeas_match:
        latest_tma["cikeas"] = get_last_tma_number(cikeas_match.group(1))

    # 3. Seksi P2C (Pertemuan Cileungsi - Cikeas)
    p2c_match = re.search(r'(?:pertemuan cileungsi\s*-\s*cikeas|p2c)\s*\n(.*?)(?=\(jika|ket:|\n\n\n|\Z)', text_lower, re.DOTALL)
    if p2c_match:
        latest_tma["p2c"] = get_last_tma_number(p2c_match.group(1))

    return latest_tma


def agent_3_tma(state: FloodState) -> FloodState:
    print("\n[Agent 3] Membedah TMA Real-time Jam Terakhir & Logika Hidrologi BPBD...")
    
    # Ambil teks laporan KP2C langsung dari Agent 2 (raw_social_data)
    combined_report_text = ""
    raw_social = state.get("raw_social_data", {})
    field_reports_data = state.get("field_reports", "")

    if isinstance(raw_social, dict) and "data" in raw_social:
        combined_report_text = raw_social["data"].get("text", "")
    elif isinstance(raw_social, str) and raw_social:
        combined_report_text = raw_social
    elif field_reports_data:
        if isinstance(field_reports_data, list):
            combined_report_text = "\n".join(field_reports_data)
        else:
            combined_report_text = str(field_reports_data)
    
    # Ekstrak angka TMA aktual jam terakhir
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

    # Audit Log
    raw_audit_logs = state.get("raw_audit_logs", {})
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
        "travel_time_hours": travel_time,
        "raw_audit_logs": raw_audit_logs
    }

