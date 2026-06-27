from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn

app = FastAPI()

# GÜVENLİK DUVARINI (CORS) TAMAMEN AÇIYORUZ
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
    DEPLOYMENT_ID = "63a2ddb70" # Senin bulduğun ID'yi buraya tam yaz

    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [{"role": "user", "content": incident.text}]
    }

    try:
        # Abacus'a isteği gönder
        response = requests.post(url, json=payload, timeout=15)
        ai_data = response.json()
        
        # Abacus'un döndüğü veriye göre (getChatResponse yapısı)
        if ai_data.get("success"):
            ai_answer = ai_data["result"]["content"]
            return {
                "boot_log": "[OK] AI Core Bağlantısı Başarılı",
                "final_decision": "AI STRATEJİK ANALİZ",
                "analysis": ai_answer,
                "action_plan": ["AI analizini uygulayın."],
                "veto": "Veto Yetkisi AI Denetiminde"
            }
        else:
            # Abacus başarısız olursa gelen hata mesajını göster
            error_msg = ai_data.get("error", "Bilinmeyen Abacus hatası")
            return {
                "boot_log": "⚠️ AI_RESPONSE_ERROR",
                "final_decision": "HATA",
                "analysis": f"Abacus Hatası: {error_msg}",
                "action_plan": ["Sistem parametrelerini kontrol edin."],
                "veto": "Erişim Kısıtlı"
            }

    except Exception as e:
        return {
            "boot_log": "❌ CONNECTION_FAILED",
            "final_decision": "OFFLINE",
            "analysis": f"Sunucu Hatası: {str(e)}",
            "action_plan": ["Backend loglarını kontrol edin."],
            "veto": "Veto Yetkisi Devre Dışı"
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)