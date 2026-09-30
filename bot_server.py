import os
import asyncio
import json
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from main import app as mas_app

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def format_audit_logs(raw_audit_logs: dict) -> str:
    """Membentuk tampilan audit log transparan untuk setiap agen"""
    if not raw_audit_logs:
        return "TIDAK ADA DATA AUDIT"

    text = "🔍 *LEMBAR AUDIT & VERIFIKASI DATA MENTAH (RAW DATA AUDIT)* 🔍\n"
    text += "=========================================="

    # Audit Agent 1 - BMKG
    bmkg_log = raw_audit_logs.get("agent_1_bmkg", {})
    text += "\n\n📌 *[AGENT_1_BMKG]*\n"
    text += f"• *Waktu Ambil Data* : `{bmkg_log.get('timestamp', 'N/A')}`\n"
    text += f"• *Sumber Data* : {bmkg_log.get('source', 'N/A')}\n"
    text += f"• *Data Mentah/Raw* : `{json.dumps(bmkg_log.get('raw_data', {}), ensure_ascii=False)}`\n"

    # Audit Agent 2 - Social / Telegram KP2C
    social_log = raw_audit_logs.get("agent_2_social", {})
    text += "\n📌 *[AGENT_2_SOCIAL]*\n"
    text += f"• *Waktu Ambil Data* : `{social_log.get('timestamp', 'N/A')}`\n"
    text += f"• *Sumber Data* : {social_log.get('source', 'N/A')}\n"
    text += f"• *Data Mentah/Raw* : `{json.dumps(social_log.get('raw_data', {}), ensure_ascii=False)}`\n"

    # Audit Agent 3 - Hydrology / TMA
    tma_log = raw_audit_logs.get("agent_3_tma", {})
    text += "\n📌 *[AGENT_3_HYDROLOGY]*\n"
    text += f"• *Waktu Ambil Data* : `{tma_log.get('timestamp', 'N/A')}`\n"
    text += f"• *Sumber Data* : {tma_log.get('source', 'N/A')}\n"
    text += f"• *Data Mentah/Raw* : `{json.dumps(tma_log.get('raw_data', {}), ensure_ascii=False)}`\n"

    text += "\n==========================================\n\n"
    return text


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌊 *Selamat Datang di Bot Pemantau Banjir Bekasi-Cileungsi-Cikeas*\n\n"
        "Gunakan perintah /cek untuk menjalankan Multi-Agent System (MAS) "
        "beserta Lembar Audit Transparansi Data Mentah."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def cek_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    status_msg = await update.message.reply_text(
        "⏳ *Memproses Multi-Agent System (MAS)...*\n[Agent 1-4 sedang bekerja narik data BMKG & KP2C]", 
        parse_mode="Markdown"
    )
    
    try:
        # Eksekusi LangGraph MAS
        result = mas_app.invoke({})
        
        # 1. Ambil & Format Lembar Audit Transparansi Agen
        raw_audit_logs = result.get("raw_audit_logs", {})
        audit_text = format_audit_logs(raw_audit_logs)
        
        # 2. Ambil Narasi Evaluasi Akhir (Agent 4)
        warning_statement = result.get("warning_statement", "Gagal memproses narasi evaluasi.")
        
        # Gabungkan Tampilan Utuh persis seperti di Termux
        full_report = f"{audit_text}📢 *OUTPUT EVALUASI AKHIR (UNTUK STAKEHOLDER)*\n==========================================\n{warning_statement}"
        
        # Kirim ke Telegram (Aman terhadap batas panjang karakter Telegram)
        if len(full_report) > 4000:
            await update.message.reply_text(audit_text, parse_mode="Markdown")
            await update.message.reply_text(f"📢 *OUTPUT EVALUASI AKHIR*\n==========================================\n{warning_statement}")
        else:
            await update.message.reply_text(full_report, parse_mode="Markdown")
            
        await status_msg.delete()
        
    except Exception as e:
        await update.message.reply_text(f"❌ Terjadi kesalahan: {str(e)}")


def main():
    if not BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN belum diisi di file .env")
        return

    print("🤖 Telegram Bot Listener (dengan Audit Log) berjalan di Termux...")
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("cek", cek_command))
    application.run_polling()


if __name__ == "__main__":
    main()

