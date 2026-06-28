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
    
    # ABACUS'UN "KESİN" İSTEDİĞİ FORMAT (is_user ve text)
    messages_payload = [
        {
            "is_user": True,
            "text": str(incident.text)
        }
    ]
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": messages_payload
    }

    try:
        # json parametresi requests kütüphanesinde listeyi otomatik JSON array'e çevirir.
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages_from_api = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages_from_api):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except:
                    pass
            
            return {"report": raw_text, "status": "text"}
        
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}
    except Exception as e:
        return {"report": f"Sunucu Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)