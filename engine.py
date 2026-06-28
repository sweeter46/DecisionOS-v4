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
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # DİĞER YAPAY ZEKANIN VE ABACUS'UN İSTEDİĞİ MANUEL LİSTE (JSON ARRAY)
    # is_user ve text anahtarlarını (keys) kesinlikle küçük harf ve doğru tipte veriyoruz.
    msg_list = []
    msg_list.append({
        "is_user": True,
        "text": str(incident.text)
    })
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": msg_list
    }

    # DİĞER YZ'NİN DEDİĞİ GİBİ: KESİN JSON STRINGIFY (json.dumps)
    json_payload = json.dumps(payload)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # DATA= kullanarak ham string gönderiyoruz, requests'in veriyi değiştirmesine izin vermiyoruz.
        response = requests.post(url, data=json_payload, headers=headers, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            # Dashboard JSON ayıklama
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except: pass
            
            return {"report": raw_text, "status": "text"}
        
        # Abacus'tan gelen hata mesajını doğrudan ekrana basıyoruz
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}
    
    except Exception as e:
        return {"report": f"Proxy Sunucu Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)