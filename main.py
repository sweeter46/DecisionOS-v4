from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn

app = FastAPI()

# CORS Ayarları: Sayfanın sunucuyla konuşmasına izin verir
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
    # ABACUS.AI BİLGİLERİ (Buraları kendi bilgilerinle doldur)
    DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
    DEPLOYMENT_ID = "685958564177fe899cd68b64e5f7fe1b" # Bu ID'yi kontrol et
    
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [{"role": "user", "content": incident.text}]
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        ai_data = response.json()
        
        if ai_data.get("success"):
            ai_answer = ai_data["result"]["content"]
            return {
                "boot_log": "[OK] DecisionHub v1.0 AI Core Yayında",
                "final_decision": "AI STRATEJİK ANALİZ",
                "analysis": ai_answer,
                "action_plan": ["AI analizini aşağıdan takip edin."],
                "veto": "AI Denetimi Aktif"
            }
        else:
            return {
                "boot_log": "⚠️ AI_ERROR",
                "final_decision": "HATA",
                "analysis": f"Abacus Hatası: {ai_data.get('error')}",
                "action_plan": ["Sistem parametrelerini kontrol edin."],
                "veto": "Erişim Kısıtlı"
            }
    except Exception as e:
        return {
            "boot_log": "❌ CONNECTION_FAILED",
            "final_decision": "OFFLINE",
            "analysis": f"Sunucu Hatası: {str(e)}",
            "action_plan": ["Bağlantıyı kontrol edin."],
            "veto": "Devre Dışı"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)