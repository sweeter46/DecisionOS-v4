from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
    DEPLOYMENT_ID = "63a2ddb70" 
    
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

        # --- AKILLI JSON PARÇALAYICI ---
        try:
            # AI'dan gelen metnin içindeki JSON'u bul ve temizle
            json_str = raw_content
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0]
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0]
            
            parsed_ai = json.loads(json_str.strip())
            
            return {
                "boot_log": parsed_ai.get("boot_log", "[SYSTEM_SYNC] AI Aktif"),
                "final_decision": parsed_ai.get("final_decision", "ANALİZ EDİLDİ"),
                "analysis": parsed_ai.get("analysis", ""),
                "action_plan": parsed_ai.get("action_plan", ["Plan metin içinde belirtildi."]),
                "veto": parsed_ai.get("veto", "VETO Kararı Belirlendi")
            }
        except:
            # Eğer AI JSON döndürmezse, her şeyi Analysis kutusuna dök (Güvenli Mod)
            return {
                "boot_log": "[RAW_DATA_MODE] Detaylı Sentez",
                "final_decision": "DETAYLI STRATEJİ",
                "analysis": raw_content,
                "action_plan": ["0-1h: Yukarıdaki analizi inceleyin.", "24h: Kriz masasını bilgilendirin."],
                "veto": "Analiz metninde detaylandırılmıştır."
            }
            
    except Exception as e:
        return {"boot_log": "❌ HATA", "final_decision": "OFFLINE", "analysis": str(e), "action_plan": [], "veto": "Hata"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)