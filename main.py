from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
import re

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
    DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
    DEPLOYMENT_ID = "685958564177fe899cd68b64e5f7fe1b" 
    
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [{"role": "user", "content": incident.text}]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        raw_content = ai_data.get("result", {}).get("content", "")

        # --- GÜÇLENDİRİLMİŞ JSON AYIKLAYICI ---
        try:
            # Metnin içinden JSON objesini cımbızla çekiyoruz
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if json_match:
                parsed_ai = json.loads(json_match.group())
                return {
                    "boot_log": parsed_ai.get("boot_log", "[OK] AI Core Synced"),
                    "final_decision": parsed_ai.get("final_decision", "KARAR ÜRETİLDİ"),
                    "analysis": parsed_ai.get("analysis", "Analiz metni sentezleniyor..."),
                    "action_plan": parsed_ai.get("action_plan", ["Plan metin içinde mevcut."]),
                    "veto": parsed_ai.get("veto", "VETO Denetimi Aktif")
                }
            raise Exception("JSON not found")
        except:
            # AI JSON göndermezse, her şeyi Analysis kutusuna döküyoruz
            return {
                "boot_log": "[RAW_MODE] Direkt Veri Akışı",
                "final_decision": "DETAYLI STRATEJİ",
                "analysis": raw_content, # Tüm metni buraya koyduk
                "action_plan": ["0-1h: Yukarıdaki analizi detaylıca inceleyin."],
                "veto": "Analiz metninde yasaklı işlemler belirtilmiştir."
            }
            
    except Exception as e:
        return {"boot_log": "❌ HATA", "final_decision": "OFFLINE", "analysis": str(e), "action_plan": [], "veto": "Bağlantı Hatası"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)