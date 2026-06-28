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
    
    # DİĞER YZ'NİN ÖNERDİĞİ TÜM FORMAT VARYANTLARI
    candidate_messages = [
        [{"is_user": True, "text": user_text}],              # Varyant 1: is_user/text (Orjinal)
        [{"role": "user", "content": user_text}],            # Varyant 2: role/content (OpenAI)
        [{"role": "user", "content": [{"type": "text", "text": user_text}]}], # Varyant 3: Nested
        [user_text]                                          # Varyant 4: Basit liste
    ]

    last_error_response = None

    for idx, msgs in enumerate(candidate_messages, start=1):
        payload = {
            "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
            "deploymentId": "63a2ddb70",
            "messages": msgs
        }
        
        try:
            logger.info(f"DENEY DENEME {idx}: Abacus'a giden veri paketleniyor...")
            r = requests.post(url, json=payload, timeout=60)
            ai_data = r.json()

            if ai_data.get("success"):
                logger.info(f"BAŞARILI! Varyant {idx} kapıyı açtı.")
                
                # Yanıtı çözümleme
                result = ai_data.get("result", {})
                messages_out = result.get("messages", [])
                raw_text = ""
                
                for m in reversed(messages_out):
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
                last_error_response = ai_data.get("error")
                logger.warning(f"Varyant {idx} reddedildi: {last_error_response}")

        except Exception as e:
            last_error_response = str(e)
            logger.error(f"Sistem Hatası (Varyant {idx}): {last_error_response}")

    # Hepsi başarısız olursa en son hatayı döndür
    return {
        "report": f"Denediğimiz 4 format da reddedildi. Son hata: {last_error_response}",
        "status": "error"
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)