import os
from datetime import datetime
from dotenv import load_dotenv
from state import FloodState

load_dotenv()

# Dual Import compatibility (PC Fedora & Termux)
try:
    from langchain_openai import ChatOpenAI
except ImportError:
    from langchain_community.chat_models import ChatOpenAI

# Ambil API key dan base URL dari .env
api_key = os.getenv("VIKEY_API_KEY") or os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE") or "https://api.vikey.ai/v1"

# Menggunakan model gemini-3.8-flash resmi dari Vikey API
llm = ChatOpenAI(
    model_name="gemini/gemini-3.8-flash",  # Atau bisa diganti "gpt-5.6-luna"
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

    # 1. Logika Deterministik Status Risiko
    if "SIAGA" in tma_status or "WASPADA" in tma_status:
        risk_level = "WASPADA"
    elif "BMKG Alert" in hulu_forecast or "Hujan Lebat" in hulu_forecast:
        risk_level = "WASPADA (Peringatan Cuaca Ekstrem Hulu)"
    else:
        risk_level = "AMAN"

    # 2. Prompt Engineering Khusus (Sumber: Telegram KP2C & BMKG)
    system_prompt = (
        "Kamu adalah Asisten Ahli Kebencanaan BPBD & Komunitas Peduli Cileungsi Cikeas (KP2C). "
        "Tugasmu adalah menyusun Laporan Peringatan Dini Banjir yang informatif, tenang, dan akurat untuk warga.\n\n"
        "SUMBER DATA DITERIMA:\n"
        "1. Laporan Pemantauan TMA Real-time dari Kanal Resmi Telegram KP2C.\n"
        "2. Peringatan Dini Cuaca Ekstrem dari BMKG.\n\n"
        "ATURAN PENULISAN:\n"
        "- Tegaskan bahwa data Tinggi Muka Air (TMA) diperoleh langsung dari pemantauan live Telegram KP2C.\n"
        "- Sebutkan status risiko, angka TMA di Hulu Cileungsi, Hulu Cikeas, dan P2C.\n"
        "- Sertakan estimasi waktu tempuh air jika ada potensi peningkatan TMA.\n"
        "- Berikan himbauan yang menenangkan namun tetap waspada untuk warga bantaran sungai (Bojongkulur, Villa Nusa Indah, Jatiasih, PGP, Kemang Pratama)."
    )

    user_prompt = (
        f"Susun laporan peringatan dini berdasarkan data berikut:\n"
        f"- Status Risiko Sistem: {risk_level}\n"
        f"- Status TMA & Sungai: {tma_status}\n"
        f"- Estimasi Waktu Tempuh Air: {travel_time} Jam\n"
        f"- Data Peringatan Cuaca BMKG: {hulu_forecast}\n"
    )

    # 3. Generate Narasi via LLM dengan Proteksi Fallback
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
            f"- {tma_status}\n"
            f"- Estimasi Waktu Tempuh Air: {travel_time} Jam\n\n"
            f"INFO CUACA HULU (Sumber: BMKG):\n"
            f"{hulu_forecast}\n\n"
            f"HIMBAUAN WARGA:\n"
            f"Warga di sepanjang bantaran sungai (Bojongkulur, Villa Nusa Indah, Jatiasih, PGP, Kemang Pratama) "
            f"diimbau untuk tetap tenang namun waspada serta terus memantau pembaruan data berkala dari KP2C dan BPBD."
        )

    return {
        "flood_risk_level": risk_level,
        "warning_statement": warning_statement
    }
