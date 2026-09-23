import os
import re
import requests
from datetime import datetime
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from state import FloodState

load_dotenv()

# Gemini 3.8 Flash Vision untuk OCR Infografis KP2C
llm_vision = ChatOpenAI(
    model="gemini/gemini-3.8-flash",
    openai_api_key=os.getenv("VIKEY_API_KEY"),
    openai_api_base="https://api.vikey.ai/v1",
    temperature=0.0
)

def fetch_kp2c_authenticated_mobile():
    """
    Menarik twit real-time @kp2c_info menggunakan cookie sesi mobile (auth_token & ct0).
    Sangat stabil running di Termux Android tanpa terhalang Cloudflare/Anti-Bot.
    """
    auth_token = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")

    # Layer 1: Authenticated Session Request ke GraphQL X
    if auth_token and ct0:
        print("[Agent 2 Engine] Menggunakan Authenticated Mobile Session Cookie...")
        headers = {
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwI380W1vm2EGGv%2BE47scaB54%3DDAODNO2126234234234234234",
            "x-csrf-token": ct0,
            "cookie": f"auth_token={auth_token}; ct0={ct0}",
            "user-agent": "Mozilla/5.0 (Android 14; Mobile; lg-g7; rv:124.0) Gecko/124.0 Firefox/124.0"
        }
        try:
            # Query User Tweets KP2C via GraphQL Endpoint
            url = "https://x.com/i/api/graphql/sK9-vK.../UserTweets?variables=%7B%22userId%22%3A%223089858532%22%2C%22count%22%3A5%7D"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                # Parsing tweet text & image media
                instructions = data['data']['user']['result']['timeline_v2']['timeline']['instructions']
                for inst in instructions:
                    if inst.get('type') == 'TimelineAddEntries':
                        entries = inst.get('entries', [])
                        if entries:
                            tweet_data = entries[0]['content']['itemContent']['tweet_results']['result']['legacy']
                            tweet_text = tweet_data.get('full_text', '')
                            
                            img_url = None
                            media_list = tweet_data.get('entities', {}).get('media', [])
                            if media_list:
                                img_url = media_list[0].get('media_url_https')
                                
                            return tweet_text, img_url, "X Official Mobile API (Authenticated)"
        except Exception as e:
            print(f"[Agent 2 Auth Fetch Error]: {e}")

    # Layer 2: Public Telegram Channel Mirror KP2C (Backup Otomatis jika Cookie Belum Diisi)
    print("[Agent 2 Engine] Memanggil Fallback Telegram Channel @kp2c_info...")
    try:
        tg_headers = {
            "User-Agent": "Mozilla/5.0 (Android 14; Mobile; rv:124.0) Gecko/124.0 Firefox/124.0"
        }
        res = requests.get("https://t.me/s/kp2c_info", headers=tg_headers, timeout=10)
        if res.status_code == 200:
            soup = BeautifulSoup(res.content, "html.parser")
            messages = soup.find_all("div", class_="tgme_widget_message_text")
            if messages:
                last_msg = messages[-1].get_text(separator="\n").strip()
                
                img_url = None
                photos = soup.find_all("a", class_="tgme_widget_message_photo_wrap")
                if photos:
                    style = photos[-1].get("style", "")
                    img_match = re.search(r"url\('([^']+)'\)", style)
                    if img_match:
                        img_url = img_match.group(1)
                        
                return last_msg, img_url, "KP2C Telegram Public Feed (Live)"
    except Exception as e:
        print(f"[Agent 2 Telegram Error]: {e}")

    return None, None, "Fetch Failed"


def run_gemini_vision_ocr(image_url: str) -> str:
    """Proses Vision OCR gambar infografis via Gemini 3.8 Flash"""
    print(f"[Agent 2 OCR] Scanning infografis via Gemini 3.8 Flash Vision...")
    try:
        message = HumanMessage(
            content=[
                {
                    "type": "text", 
                    "text": (
                        "Ini adalah gambar infografis laporan TMA dari KP2C. "
                        "Bacakan rincian data: Tanggal Laporan, serta nilai TMA (Tinggi Muka Air) dalam cm "
                        "dan kondisi cuaca pada jam pemantauan TERAKHIR untuk 3 lokasi: "
                        "Hulu Cileungsi, Hulu Cikeas, dan P2C (Pertemuan)."
                    )
                },
                {"type": "image_url", "image_url": {"url": image_url}},
            ]
        )
        response = llm_vision.invoke([message])
        return response.content
    except Exception as e:
        return f"Gagal OCR Gambar: {str(e)}"


def agent_2_social(state: FloodState) -> FloodState:
    print("\n[Agent 2] Menarik Laporan Live KP2C secara Dinamis...")
    
    tweet_text, img_url, source_used = fetch_kp2c_authenticated_mobile()
    ocr_result = ""
    
    if tweet_text:
        final_report = f"[LAPORAN LIVE KP2C]:\n{tweet_text}"
        if img_url:
            ocr_result = run_gemini_vision_ocr(img_url)
            final_report += f"\n\n[HASIL SCAN VISION OCR INFOGRAFIS]:\n{ocr_result}"
    else:
        final_report = "Gagal mengambil data live. Memerlukan pemeriksaan cookie/network."

    audit_entry = {
        "agent_2_social": {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "source": f"KP2C Official Feed via {source_used}",
            "raw_text_fetched": tweet_text or "Fetch Failed",
            "attached_image_url": img_url,
            "gemini_ocr_extracted": ocr_result if ocr_result else "N/A"
        }
    }

    return {
        "field_reports": [final_report],
        "raw_audit_logs": audit_entry
    }
