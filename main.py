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
    # SENİN TOKEN VE ID BİLGİLERİN
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
        
        # --- EN GARANTİ VERİ OKUMA ---
        # Abacus'un döndürebileceği tüm ihtimalleri deniyoruz
        result = ai_data.get("result", {})
        report = result.get("content") or result.get("response") or ai_data.get("content")
        
        if not report:
            # Eğer hala bulamadıysak, gelen tüm cevabı metne çevir (Hata analizi için)
            report = f"AI boş cevap döndürdü veya format değişti. Gelen ham veri: {str(ai_data)}"
            
        return {"report": report}
    except Exception as e:
        return {"report": f"Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)