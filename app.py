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
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [{"is_user": True, "text": incident.text}]
    }

    try:
        response = requests.post(url, json=payload, timeout=45)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")
            
            # Kod bloklarını ve gereksiz metinleri temizle
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # İlk { ve son } arasını bul
            match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if match:
                try:
                    clean_json_str = match.group(1)
                    report_obj = json.loads(clean_json_str)
                    # HTML tarafına "is_json" bayrağını ve temiz objeyi gönder
                    return {"report": report_obj, "is_json": True}
                except:
                    pass
            
            return {"report": raw_text, "is_json": False}
        return {"report": "AI API Hatası", "is_json": False}
    except Exception as e:
        return {"report": str(e), "is_json": False}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)