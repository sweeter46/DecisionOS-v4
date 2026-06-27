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
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # ABACUS'ÜN İSTEDİĞİ EN KESİN FORMAT
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "is_user": True,
                "text": incident.text
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        
        if ai_data.get("success") == True:
            # Result objesinin içindeki içeriği alıyoruz
            result = ai_data.get("result", {})
            report = result.get("content") or result.get("text") or "Analiz tamamlandı."
            return {"report": report}
        else:
            # Abacus'ten gelen hata mesajını temizce gösterelim
            error_msg = ai_data.get("error", "Bilinmeyen bir Abacus hatası.")
            return {"report": f"Abacus Sistem Yanıtı: {error_msg}"}
            
    except Exception as e:
        return {"report": f"Sistem hatası oluştu: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)