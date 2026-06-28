from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import urllib.request
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
        data = json.dumps(payload).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='POST')
        req.add_header('Content-Type', 'application/json')
        req.add_header('Accept', 'application/json')
        
        # 403 HATASINI BİTİREN KRİTİK SATIR (KİMLİK KARTI):
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        with urllib.request.urlopen(req, timeout=60) as response:
            res_body = response.read().decode('utf-8')
            ai_data = json.loads(res_body)
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except: pass
            
            return {"report": raw_text, "status": "text"}
            
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Bağlantı Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)