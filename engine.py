import os
import requests
import json
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

# ABACUS KİMLİKLERİ
DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611" 
DEPLOYMENT_ID = "63a2ddb70"    
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    # KESİN VE MANUEL JSON İNŞASI
    # Hiçbir kütüphaneye güvenmiyoruz, string olarak tam formatı çiziyoruz.
    user_message = incident.text.replace('"', "'").replace("\n", " ") # Tırnakları temizle
    
    raw_payload = (
        '{\n'
        f'  "deploymentToken": "{DEPLOYMENT_TOKEN}",\n'
        f'  "deploymentId": "{DEPLOYMENT_ID}",\n'
        '  "messages": [\n'
        '    {\n'
        '      "is_user": true,\n'
        f'      "text": "{user_message}"\n'
        '    }\n'
        '  ]\n'
        '}'
    )

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # data=raw_payload kullanarak requests'in içeriği değiştirmesini engelliyoruz
        response = requests.post(ABACUS_URL, data=raw_payload.encode('utf-8'), headers=headers, timeout=60)
        
        logger.info(f"Abacus Status: {response.status_code}")
        ai_data = response.json()
        
        if ai_data.get("success"):
            raw_answer = ai_data.get("result", {}).get("answer", "")
            
            # --- ARINDIRMA ---
            clean = raw_answer
            junk = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial"]
            for tag in junk:
                clean = clean.replace(tag, "")
            
            clean = clean.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').strip()
            return {"analysis": clean}
            
        return {"error": f"Abacus Reddi: {ai_data.get('error')}"}

    except Exception as e:
        return {"error": f"Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)