from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
import re # Düzenli ifadeler kütüphanesi

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
        response = requests.post(url, json=payload, timeout=40)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in messages:
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            # --- TÜM PARANTEZLERİ VE ÇÖPLERİ KAZIYAN PROFESYONEL TEMİZLİK ---
            # Gereksiz ```json gibi ibareleri sil
            raw_text = raw_text.replace("```json", "").replace("```", "").strip()
            
            # Yazı içindeki ilk { ve son } arasını al
            match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
            if match:
                clean_json_str = match.group(1)
                # Metni gerçek bir Python objesine çevir
                clean_data = json.loads(clean_json_str)
                return {"report": clean_data, "is_json": True}
            
            return {"report": raw_text, "is_json": False}
        return {"report": "Abacus Hatası", "is_json": False}
    except Exception as e:
        return {"report": str(e), "is_json": False}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)