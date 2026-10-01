import os
from datetime import datetime
from dotenv import load_dotenv
from state import FloodState

load_dotenv()

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_community.chat_models import ChatOpenAI

api_key = os.getenv("VIKEY_API_KEY") or os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE") or "https://api.vikey.ai/v1"

llm = ChatOpenAI(
    model_name="gemini/gemini-3.8-flash",
    openai_api_base=api_base,
    openai_api_key=api_key,
    request_timeout=15,
    max_retries=1
)

def agent_4_evaluator(state: FloodState) -> FloodState:
    print("\n[Agent 4] Memproses Keputusan Akhir & Peringatan Dini via Vikey API...")
    
    hulu_forecast = state.get("hulu_forecast", "")
    tma_status = state.get("tma_status", "")
    travel_time = state.get("travel_time_hours", 0)

    parsed_tma = state.get("parsed_tma") or {}
    if not parsed_tma:
        raw_audit = state.get("raw_audit_logs") or {}
        tma_log = raw_audit.get("agent_3_tma", {})
        parsed_tma = tma_log.get("raw_data", {}).get("parsed_tma_cm", {"cileungsi": 0, "cikeas": 0, "p2c": 0})

    cil_val = parsed_tma.get("cileungsi", 0)
    cik_val = parsed_tma.get("cikeas", 0)
    p2c_val = parsed_tma.get("p2c", 0)

    if "SIAGA" in tma_status or "WASPADA" in tma_status:
        risk_level = "WASPADA"
    elif "BMKG Alert" in hulu_forecast or "Hujan Lebat" in hulu_forecast or "⚠️" in hulu_forecast:
        risk_level = "WASPADA (Peringatan Cuaca Ekstrem Hulu)"
    else:
        risk_level = "AMAN"

    system_prompt = (
        "Kamu adalah Asisten Ahli Kebencanaan BPBD & Komunitas Peduli Cileungsi Cikeas (KP2C).\n"
        "Tugasmu adalah menyusun Laporan Peringatan Dini Banjir yang informatif, tenang, dan akurat untuk warga.\n\n"
        "ATURAN WAJIB DITURUTI:\n"
        "1. WAJIB mencantumkan angka Tinggi Muka Air (TMA) persis sesuai data aktual:\n"
        f"   - Hulu Cileungsi: {cil_val} cm\n"
        f"   - Hulu Cikeas: {cik_val} cm\n"
        f"   - Pertemuan Cileungsi Cikeas (P2C): {p2c_val} cm\n"
        "2. DILARANG HARUS/TIDAK BOLEH mengubah angka TMA menjadi 0 cm jika data input bukan 0.\n"
        "3. Tegaskan bahwa data TMA diperoleh langsung dari pemantauan live Telegram KP2C.\n"
        "4. Berikan himbauan yang menenangkan namun tetap waspada untuk warga bantaran sungai (Bojongkulur, Villa Nusa Indah, Jatiasih, PGP, Kemang Pratama)."
    )

    user_prompt = (
        f"Susun laporan peringatan dini berdasarkan data aktual berikut:\n"
        f"- Status Risiko Sistem: {risk_level}\n"
        f"- DATA TMA REAL-TIME KP2C:\n"
        f"  * Hulu Cileungsi: {cil_val} cm\n"
        f"  * Hulu Cikeas: {cik_val} cm\n"
        f"  * Pertemuan Cileungsi Cikeas (P2C): {p2c_val} cm\n"
        f"- Status Ringkasan Sungai: {tma_status}\n"
        f"- Estimasi Waktu Tempuh Air: {travel_time} Jam\n"
        f"- Data Peringatan Cuaca BMKG: {hulu_forecast}\n"
    )

    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        response = llm.invoke(messages)
        warning_statement = response.content
    except Exception as e:
        print(f"⚠️ Vikey API Error ({str(e)}). Menggunakan Narasi Fallback Template.")
        warning_statement = (
            f"--- LAPORAN PERINGATAN DINI BANJIR BEKASI ---\n"
            f"STATUS RISIKO: {risk_level}\n\n"
            f"DATA TANGKAP AIR & KALI (Sumber: Telegram KP2C):\n"
            f"- Hulu Cileungsi: {cil_val} cm\n"
            f"- Hulu Cikeas: {cik_val} cm\n"
            f"- Pertemuan Cileungsi-Cikeas (P2C): {p2c_val} cm\n"
            f"- Estimasi Waktu Tempuh Air: {travel_time} Jam\n\n"
            f"INFO CUACA HULU (Sumber: BMKG):\n"
            f"{hulu_forecast}\n\n"
            f"HIMBAUAN WARGA:\n"
            f"Warga di sepanjang bantaran sungai (Bojongkulur, Villa Nusa Indah, Jatiasih, PGP, Kemang Pratama) "
            f"diimbau untuk tetap tenang namun waspada serta terus memantau pembaruan data berkala dari KP2C dan BPBD."
        )

    return {
        "flood_risk_level": risk_level,
        "warning_statement": warning_statement,
        "parsed_tma": parsed_tma
    }
