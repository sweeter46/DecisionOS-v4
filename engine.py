from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
import uvicorn
import re
import logging

# Logları Render konsolunda görmek için aktif ediyoruz
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    user_text = str(incident.text or "")
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # ABACUS'UN KABUL EDEBİLECEĞİ TÜM OLASI FORMATLAR
    candidate_messages = [
        [{"is_user": True, "text": user_text}],             # Variant A: is_user/text (Resmi format)
        [{"role": "user", "content": user_text}],           # Variant B: role/content (OpenAI standardı)
        [{"role": "user", "content": [{"type": "text", "text": user_text}]}], # Variant C: Nested
        [user_text]                                         # Variant D: Sadece string listesi
    ]

    last_error = None

    for idx, msgs in enumerate(candidate_messages, start=1):
        payload = {
            "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
            "deploymentId": "63a2ddb70",
            "messages": msgs
        }
        
        try:
            logger.info(f"DENEME {idx}: Abacus'a hazırlanan paket gönderiliyor...")
            r = requests.post(url, json=payload, timeout=60)
            ai_data = r.json()

            if ai_data.get("success"):
                logger.info(f"BAŞARILI! Variant {idx} kapıyı açtı.")
                
                # Yanıtı Ayıkla
                messages = ai_data.get("result", {}).get("messages", [])
                raw_text = ""
                for m in reversed(messages):
                    if isinstance(m, dict):
                        raw_text = m.get("text") or m.get("content") or ""
                        if raw_text: break
                
                # Dashboard JSON Extract
                clean = raw_text.replace("```json", "").replace("```", "").strip()
                match = re.search(r'(\{.*\})', clean, re.DOTALL)
                
                if match:
                    try:
                        return {"report": json.loads(match.group(1)), "status": "success"}
                    except: pass
                
                return {"report": raw_text, "status": "text"}
            
            else:
                last_error = ai_data.get("error")
                logger.warning(f"Variant {idx} reddedildi: {last_error}")

        except Exception as e:
            last_error = str(e)
            logger.error(f"Sistem Hatası (Variant {idx}): {last_error}")

    # Hepsi başarısız olursa
    return {
        "report": f"Tüm formatlar denendi, Abacus hala reddediyor: {last_error}",
        "status": "error"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)