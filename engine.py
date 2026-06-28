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
    
    # MESAJI MANUEL OLARAK JSON FORMATINA SOKUYORUZ (GÜVENLİ YÖNTEM)
    safe_text = incident.text.replace('"', '\\"').replace('\n', '\\n')
    
    # ABACUS'ÜN REDDEDEMEYECEĞİ TAM HAM METİN (RAW BODY)
    raw_payload = '{' + \
        '"deploymentToken": "f3baa2a32be542f9af98a81aa71da611",' + \
        '"deploymentId": "63a2ddb70",' + \
        f'"messages": [{{"is_user": true, "text": "{safe_text}"}}]' + \
    '}'

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # data= parametresiyle ham metni hiç bozmadan gönderiyoruz
        response = requests.post(url, data=raw_payload.encode('utf-8'), headers=headers, timeout=60)
        ai_data = response.json()
        
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
                except:
                    pass
            
            return {"report": raw_text, "status": "text"}
        
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Bağlantı Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)