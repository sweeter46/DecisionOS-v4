from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
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
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # KESİN ÇÖZÜM: Payload yapısını Abacus'un beklediği liste formatına sabitledik.
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
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            if not raw_text:
                return {"report": "AI boş yanıt döndürdü.", "status": "error"}

            # Gereksiz markdown ve JSON etiketlerini temizle
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # Yazı içindeki JSON objesini ayıkla
            match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
            
            if match:
                try:
                    report_obj = json.loads(match.group(1))
                    return {"report": report_obj, "status": "success"}
                except:
                    pass
            
            return {"report": raw_text, "status": "text"}
        
        return {"report": f"Abacus API Hatası: {ai_data.get('error')}", "status": "error"}
    except Exception as e:
        return {"report": f"Sistem hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)