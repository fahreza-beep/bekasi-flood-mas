import json
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from state import FloodState
from agents.agent_bmkg import agent_1_bmkg
from agents.agent_social import agent_2_social
from agents.agent_tma import agent_3_tma
from agents.agent_evaluator import agent_4_evaluator

load_dotenv()

workflow = StateGraph(FloodState)

workflow.add_node("bmkg_agent", agent_1_bmkg)
workflow.add_node("social_agent", agent_2_social)
workflow.add_node("tma_agent", agent_3_tma)
workflow.add_node("evaluator_agent", agent_4_evaluator)

workflow.add_edge(START, "bmkg_agent")
workflow.add_edge(START, "social_agent")
workflow.add_edge("bmkg_agent", "tma_agent")
workflow.add_edge("social_agent", "tma_agent")
workflow.add_edge("tma_agent", "evaluator_agent")
workflow.add_edge("evaluator_agent", END)

app = workflow.compile()

if __name__ == "__main__":
    print("==========================================================")
    print(" 🌊 MULTI-AGENT SYSTEM (MAS) BANJIR CILEUNGSI-BEKASI 🌊 ")
    print("==========================================================")
    
    result = app.invoke({})
    
    # 🔍 LEMBAR VERIFIKASI DATA MENTAH (RAW DATA AUDIT TRAIL)
    print("\n" + "🔍 "*15)
    print(" LEMBAR AUDIT & VERIFIKASI DATA MENTAH (RAW DATA TRAIL) ")
    print("🔍 "*15)
    
    logs = result.get("raw_audit_logs", {})
    for agent_name, audit_info in logs.items():
        print(f"\n📌 [{agent_name.upper()}]")
        print(f"   • Waktu Ambil Data : {audit_info.get('timestamp')}")
        print(f"   • Sumber Data      : {audit_info.get('source', 'Internal Calculation')}")
        print(f"   • Data Mentah/Raw  : {json.dumps(audit_info.get('raw_payload_summary') or audit_info.get('raw_text_fetched') or audit_info.get('parsed_numbers'), indent=6, ensure_ascii=False)}")
    
    print("\n" + "="*58)
    print(" 📢 OUTPUT EVALUASI AKHIR (UNTUK STAKEHOLDER / WARGA)")
    print("="*58)
    print(result.get("warning_statement"))
