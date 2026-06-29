import os
import requests
import json
import logging
import re
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

# --- GÜNCELLENMİŞ ABACUS KİMLİKLERİ ---
DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611" 
DEPLOYMENT_ID = "63a2ddb70"    
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    # Requests kütüphanesi json=payload ile double-encoding'i engeller
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [
            {
                "is_user": True, 
                "text": str(incident.text).strip()
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "DecisionOS-Architect/3.0"
    }

    try:
        response = requests.post(ABACUS_URL, json=payload, headers=headers, timeout=60)
        logger.info(f"Abacus Yanıt Kodu: {response.status_code}")
        ai_data = response.json()
        
        if ai_data.get("success"):
            raw_text = ai_data.get("result", {}).get("answer", "")
            
            # --- ARINDIRMA MOTORU ---
            clean = raw_text
            
            # report_content alanını ayıkla
            if "report_content" in clean:
                try:
                    clean = clean.split("report_content", 1)[-1].strip(": \"'{}[]")
                except:
                    pass
            
            # Teknik etiket kırıntılarını temizle
            junk_tags = ["evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial", "boot_log"]
            for tag in junk_tags:
                clean = clean.replace(tag, "")
            
            # Final karakter temizliği
            clean = clean.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').replace('\\', '').replace(':', '').strip()
            
            return {"analysis": clean}
            
        return {"error": f"Abacus Hatası: {ai_data.get('error')}"}

    except Exception as e:
        logger.error(f"Sistem Hatası: {str(e)}")
        return {"error": f"Sistem Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)