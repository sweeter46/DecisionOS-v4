from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
import re

app = FastAPI()

# Tarayıcı izinlerini en geniş kapsamda açıyoruz
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
    
    # ABACUS'UN KESİN İSTEDİĞİ LİSTE FORMATI: [ { "is_user": True, "text": "..." } ]
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "is_user": True,
                "text": str(incident.text)
            }
        ]
    }

    try:
        # Zaman aşımını 60 saniye yapıyoruz ki AI rahat düşünsün
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            # En son gelen asistan mesajını tersten arayarak bul
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            if not raw_text:
                return {"report": "AI boş yanıt döndürdü.", "status": "error"}

            # Gereksiz JSON etiketlerini temizle
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # Yazı içindeki JSON objesini ara
            match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
            
            if match:
                try:
                    report_obj = json.loads(match.group(1))
                    return {"report": report_obj, "status": "success"}
                except:
                    pass
            
            # Eğer JSON formatı yoksa düz metin olarak gönder
            return {"report": raw_text, "status": "text"}
        
        # Abacus'tan gelen hata mesajını doğrudan döndür
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}
        
    except Exception as e:
        return {"report": f"Sunucu Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    # Render'ın verdiği portu yakala
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)