import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from state import FloodState

load_dotenv()

# Menggunakan Vikey API (OpenAI Compatible Endpoint)
llm = ChatOpenAI(
    model="gemini/gemini-3.8-flash",
    openai_api_key=os.getenv("VIKEY_API_KEY"),
    openai_api_base="https://api.vikey.ai/v1",
    temperature=0.1
)

def agent_4_evaluator(state: FloodState) -> FloodState:
    print("\n[Agent 4] Memproses Keputusan Akhir & Peringatan Dini via Vikey API...")
    
    hulu_forecast = state.get("hulu_forecast", "Tidak ada data BMKG")
    field_reports = state.get("field_reports", ["Tidak ada data sosial media"])
    tma_status = state.get("tma_status", "Status TMA belum dihitung")
    travel_time = state.get("travel_time_hours", 0.0)
    
    prompt = f"""
    Kamu adalah sistem Peringatan Dini Banjir (Early Warning System) resmi untuk DAS Cileungsi - Cikeas - Kali Bekasi.
    
    RINGKASAN DATA FAKTUAL (REAL-TIME):
    1. BMKG Weather Alert:
       {hulu_forecast}
       
    2. Laporan KP2C & Hasil OCR Gambar X:
       {field_reports}
       
    3. Status Evaluasi TMA (Agent 3) & Travel Time:
       {tma_status} | Estimasi Tiba di Bekasi: {travel_time} Jam
    
    INSTRUKSI UTAMA (ANTI-HALLUCINATION):
    - Sebutkan angka TMA aktual (dalam cm) yang terbaca di laporan untuk Cileungsi, Cikeas, dan P2C.
    - Jangan menambah atau mengarang angka yang tidak ada pada Ringkasan Data di atas.
    - Tentukan Tingkat Risiko Keseluruhan (AMAN / WASPADA / SIAGA / AWAS).
    
    Format Jawaban Resmi:
    --- LAPORAN PERINGATAN DINI BANJIR BEKASI ---
    STATUS RISIKO: [AMAN / WASPADA / SIAGA / AWAS]
    DATA TMA TERBACA: [Sebutkan Rincian cm Hulu Cileungsi, Hulu Cikeas, dan P2C]
    ESTIMASI WAKTU KEDATANGAN AIR: [X Jam / Tidak Ada Potensi Limpasan]
    
    NARASI UNTUK WARGA:
    [Tulis narasi ringkas berisi situasi terkini dan imbauan/langkah yang perlu diambil warga permukiman rawan (Bojongkulur, Jatiasih, Kemang Pratama, PGP)]
    """
    
    try:
        response = llm.invoke(prompt)
        content = response.content
        
        risk_level = "AMAN"
        if "AWAS" in content:
            risk_level = "AWAS"
        elif "SIAGA" in content:
            risk_level = "SIAGA"
        elif "WASPADA" in content:
            risk_level = "WASPADA"
            
        return {
            "flood_risk_level": risk_level,
            "warning_statement": content
        }
    except Exception as e:
        return {
            "flood_risk_level": "ERROR",
            "warning_statement": f"Gagal menghasilkan laporan via Vikey API: {str(e)}"
        }
