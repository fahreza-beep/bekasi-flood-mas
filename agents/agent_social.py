import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from state import FloodState

load_dotenv()

def fetch_private_telegram_kp2c():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        return {"status": "failed", "message": "TELEGRAM_API_ID / API_HASH belum ada di .env"}

    client = TelegramClient('kp2c_session', int(api_id), api_hash)

    async def main():
        await client.connect()
        if not await client.is_user_authorized():
            await client.disconnect()
            return {"status": "failed", "message": "Belum login / OTP belum dimasukkan"}

        target_dialog = None
        async for dialog in client.iter_dialogs():
            if "kp2c" in dialog.name.lower():
                target_dialog = dialog
                break

        if not target_dialog:
            await client.disconnect()
            return {"status": "failed", "message": "Grup/Channel KP2C tidak ditemukan di daftar Telegram kamu"}

        result_data = None
        async for message in client.iter_messages(target_dialog.entity, limit=3):
            if message.text:
                result_data = {
                    "timestamp": str(message.date),
                    "text": message.text
                }
                break

        await client.disconnect()
        return {"status": "success", "data": result_data}

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(main())
        loop.close()
        return data
    except Exception as e:
        return {"status": "failed", "message": str(e)}

def agent_2_social(state: FloodState) -> FloodState:
    print("\n[Agent 2] Menarik Laporan Live KP2C via Telegram Private Channel...")

    telegram_result = fetch_private_telegram_kp2c()

    report_text = None
    if telegram_result.get("status") == "success" and telegram_result.get("data"):
        report_text = telegram_result["data"].get("text")

    raw_audit_logs = state.get("raw_audit_logs") or {}
    raw_audit_logs["agent_2_social"] = {
        "timestamp": telegram_result.get("data", {}).get("timestamp", "N/A") if isinstance(telegram_result.get("data"), dict) else "N/A",
        "source": "Private Telegram Channel KP2C",
        "raw_data": telegram_result
    }

    return {
        "field_reports": report_text,
        "raw_social_data": telegram_result,
        "raw_audit_logs": raw_audit_logs
    }
