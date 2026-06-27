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
    
    # ABACUS'UN BEKLEYEBİLECEĞİ 3 FARKLI FORMATI DENİYORUZ
    # Eğer messages listesi hata veriyorsa, 'prompt' olarak göndermeyi deneyeceğiz
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        # Chatbot formatı (Genelde bunu ister)
        "messages": [{"is_user": True, "text": incident.text}],
        # Alternatif tahmin formatı (Eğer chatbot değilse bunu ister)
        "prompt": incident.text,
        "input_data": {"text": incident.text}
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        
        # Hata Yönetimi
        if ai_data.get("success") == True:
            result = ai_data.get("result", {})
            # Cevap content, response veya text içinde olabilir
            report = result.get("content") or result.get("text") or result.get("response") or "Analiz üretildi."
            return {"report": report}
        else:
            # Burası KRİTİK: Abacus'un bize tam olarak ne hata verdiğini burada göreceğiz.
            return {"report": f"Abacus Sistem Yanıtı: {ai_data.get('error')}"}
            
    except Exception as e:
        return {"report": f"Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)