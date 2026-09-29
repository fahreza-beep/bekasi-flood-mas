import os
import asyncio
from telethon import TelegramClient

def fetch_private_telegram_kp2c():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        return {"status": "failed", "message": "TELEGRAM_API_ID / API_HASH belum diisi di .env"}

    # Nama session file yang disimpan lokal di Termux
    client = TelegramClient('kp2c_session', int(api_id), api_hash)

    try:
        async def main():
            await client.start()
            # Nama grup/channel privat KP2C di Telegram kamu
            target_chat = "Info KP2C 1"

            result_data = None
            async for message in client.iter_messages(target_chat, limit=3):
                if message.text:
                    result_data = {
                        "timestamp": str(message.date),
                        "text": message.text
                    }
                    break

            await client.disconnect()
            return result_data

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(main())
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "failed", "message": str(e)}

def agent_2_social(state):
    print("\n[Agent 2] Menarik Laporan Live KP2C via Telegram Private Channel...")

    # Memanggil fungsi scraper Telethon
    telegram_result = fetch_private_telegram_kp2c()

    # Update audit logs di dalam state
    raw_audit_logs = state.get("raw_audit_logs", {})
    raw_audit_logs["agent_2_social"] = {
        "timestamp": telegram_result.get("data", {}).get("timestamp", "N/A") if isinstance(telegram_result.get("data"), dict) else "N/A",
        "source": "Private Telegram Channel KP2C",
        "raw_data": telegram_result
    }

    state["raw_audit_logs"] = raw_audit_logs
    state["social_data"] = telegram_result
    return state
