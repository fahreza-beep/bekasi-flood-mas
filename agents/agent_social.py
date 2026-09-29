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
    
    async def main():
        await client.start()
        # Masukkan NAMA GRUP / ID CHANNEL PRIVAT di sini
        # Kamu bisa pakai judul lengkap grupnya atau ID angka (-100xxxx)
        target_chat = "Info KP2C 1"  # Sesuaikan dengan nama persis grup/channel privat kamu
        
        async for message in client.iter_messages(target_chat, limit=3):
            if message.text:
                return {
                    "timestamp": str(message.date),
                    "text": message.text
                }
        return None

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        data = loop.run_until_complete(main())
        client.disconnect()
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "failed", "message": str(e)}
