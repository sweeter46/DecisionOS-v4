from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
import uvicorn
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
    # ABACUS API BİLGİLERİ (DOĞRUDAN PARAMETRE OLARAK)
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    token = "f3baa2a32be542f9af98a81aa71da611"
    id = "63a2ddb70"

    payload = {
        "deploymentToken": token,
        "deploymentId": id,
        "messages": [
            {
                "is_user": True,
                "text": str(incident.text)
            }
        ]
    }

    try:
        # json= kullanarak verinin otomatik LISTE/ARRAY olarak gitmesini sağlıyoruz
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            # En son AI mesajını bul
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            # JSON Ayıklama
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except: pass
            
            return {"report": raw_text, "status": "text"}
            
        return {"report": f"Abacus Reddi: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Sistem Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)