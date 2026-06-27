from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json # Yeni eklendi

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
    
    # ABACUS'ÜN EN KATI LİSTE FORMATI
    # Veriyi Python objesi olarak değil, doğrudan JSON metni olarak mühürlüyoruz
    messages_list = [{"is_user": True, "text": incident.text}]
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": messages_list # Standart liste gönderimi
    }

    try:
        # İLK DENEME: Standart JSON gönderimi
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        
        # EĞER HALA LİSTE HATASI VERİRSE (OTOMATİK İKİNCİ DENEME)
        if ai_data.get("error") and "must be a list" in ai_data.get("error"):
            # Bazı API'ler messages'ı string içinde liste olarak bekler
            payload["messages"] = json.dumps(messages_list) 
            response = requests.post(url, json=payload, timeout=30)
            ai_data = response.json()

        if ai_data.get("success") == True:
            result = ai_data.get("result", {})
            report = result.get("content") or result.get("text") or "Analiz başarıyla sentezlendi."
            return {"report": report}
        else:
            return {"report": f"Abacus Sistem Yanıtı: {ai_data.get('error')}"}
            
    except Exception as e:
        return {"report": f"Sistem hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)