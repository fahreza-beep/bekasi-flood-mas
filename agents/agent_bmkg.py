import requests
import xmltodict
from datetime import datetime
from state import FloodState

BMKG_NOWCAST_URL = "https://www.bmkg.go.id/alerts/nowcast/id"

TARGET_KECAMATAN = [
    "babakan madang", "sukamakmur", "citeureup", "tajur",
    "megamendung", "cisarua", "sukaraja",
    "cileungsi", "gunung putri", "klapanunggal",
    "bantar gebang", "jatiasih", "bekasi selatan", "bekasi timur", "rawalumubu"
]

def fetch_bmkg_alerts_kp2c_area():
    try:
        response = requests.get(BMKG_NOWCAST_URL, timeout=10)
        if response.status_code != 200:
            return "Gagal mengambil data dari API BMKG."

        data = xmltodict.parse(response.content)
        items = data.get('rss', {}).get('channel', {}).get('item', [])

        if not items:
            return "Tidak ada peringatan dini cuaca aktif dari BMKG saat ini."

        if isinstance(items, dict):
            items = [items]

        relevant_alerts = []
        for item in items:
            title = item.get('title', '').lower()
            desc = item.get('description', '').lower()

            matched_areas = [kec.title() for kec in TARGET_KECAMATAN if kec in title or kec in desc]

            if matched_areas:
                alert_info = (
                    f"⚠️ [BMKG Alert - DAS Cileungsi/Cikeas]\n"
                    f"Kecamatan Terdampak: {', '.join(set(matched_areas))}\n"
                    f"Detail: {item.get('description')}\n"
                    f"Waktu Rilis: {item.get('pubDate')}"
                )
                relevant_alerts.append(alert_info)

        return "\n\n".join(relevant_alerts) if relevant_alerts else "KONDISI KONDUSIF: Tidak terdeteksi peringatan dini cuaca ekstrem BMKG untuk kecamatan Hulu-Hilir Cileungsi, Cikeas, maupun Bekasi."

    except Exception as e:
        return f"Error saat membaca feed BMKG: {str(e)}"

def agent_1_bmkg(state: FloodState) -> FloodState:
    print("\n[Agent 1] Menarik Peringatan Dini BMKG khusus Wilayah Cileungsi-Cikeas-Bekasi...")
    forecast_data = fetch_bmkg_alerts_kp2c_area()

    audit_entry = {
        "agent_1_bmkg": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": BMKG_NOWCAST_URL,
            "raw_payload_summary": forecast_data
        }
    }

    return {
        "hulu_forecast": forecast_data,
        "raw_audit_logs": audit_entry
    }
