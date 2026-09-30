import json
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from state import FloodState
from agents.agent_bmkg import agent_1_bmkg
from agents.agent_social import  agent_2_social
from agents.agent_tma import agent_3_tma
from agents.agent_evaluator import agent_4_evaluator

load_dotenv()

workflow = StateGraph(FloodState)

# 1. Registrasi Semua Node
workflow.add_node("bmkg_agent", agent_1_bmkg)
workflow.add_node("social_agent", agent_2_social)
workflow.add_node("tma_agent", agent_3_tma)
workflow.add_node("evaluator_agent", agent_4_evaluator)

# 2. Tentukan Titik Awal (Entry Point)
workflow.set_entry_point("bmkg_agent")

# 3. Hubungkan Alur Kerja Sekuensial (Setiap Node Memiliki Jalur Masuk & Keluar)
workflow.add_edge("bmkg_agent", "social_agent")
workflow.add_edge("social_agent", "tma_agent")
workflow.add_edge("tma_agent", "evaluator_agent")
workflow.add_edge("evaluator_agent", END)

# 4. Compile Graph
app = workflow.compile()

if __name__ == "__main__":
    print("==================================================")
    print(" 🌊 MULTI-AGENT SYSTEM (MAS) BANJIR CILEUNGSI-CITEUREUP")
    print("==================================================")

    result = app.invoke({})

    # 🔍 LEMBAR VERIFIKASI DATA MENTAH (RAW DATA AUDIT LOG)
    print("\n" + "🔍 "*15)
    print(" LEMBAR AUDIT & VERIFIKASI DATA MENTAH (RAW DATA AUDIT)")
    print("🔍 "*15)

    logs = result.get("raw_audit_logs", {})
    if isinstance(logs, dict):
        for agent_name, audit_info in logs.items():
            print(f"\n📌 [{agent_name.upper()}]")
            if isinstance(audit_info, dict):
                print(f"   • Waktu Ambil Data : {audit_info.get('timestamp', 'N/A')}")
                print(f"   • Sumber Data      : {audit_info.get('source', 'N/A')}")
                print(f"   • Data Mentah/Raw  : {json.dumps(audit_info.get('raw_data', {}), ensure_ascii=False)}")
            else:
                print(f"   • Detail           : {audit_info}")

    print("\n" + "="*58)
    print(" 📢 OUTPUT EVALUASI AKHIR (UNTUK STAKEHOLDER)")
    print("="*58)
    print(result.get("warning_statement", "Tidak ada laporan peringatan."))
