from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn

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
    # ABACUS.AI BİLGİLERİ
    DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611" # Ekrandaki Token
    DEPLOYMENT_ID = "63a2ddb70" # Bulduğun ID
    
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [{"role": "user", "content": f"DecisionOS v4.0 Protokolü: {incident.text}"}]
    }

    try:
        # İstek gönderiliyor (Chatbot metodu API Key yerine Token ile çalışır)
        response = requests.post(url, json=payload)
        ai_data = response.json()
        
        # Gelen cevabı ayıklıyoruz
        ai_answer = ai_data.get("result", {}).get("content", "AI cevabı oluşturamadı.")
        
        return {
            "boot_log": "[OK] DecisionHub v1.0 AI Core Yayında",
            "final_decision": "AI STRATEJİK ANALİZ",
            "analysis": ai_answer,
            "action_plan": ["Aşağıdaki AI analizini uygulayın."],
            "veto": "AI Denetimi Aktif"
        }
    except Exception as e:
        return {
            "boot_log": "❌ BAĞLANTI HATASI",
            "final_decision": "OFFLINE",
            "analysis": f"Sistem hatası: {str(e)}",
            "action_plan": ["Bağlantıyı kontrol edin."],
            "veto": "Veto Yetkisi Devre Dışı"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)