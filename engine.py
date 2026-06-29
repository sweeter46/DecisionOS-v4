import os
import requests
import json
import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    # ABACUS'UN İSTEDİĞİ EN SAF LİSTE YAPISI
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

    # JSON'ı en sıkı ve hatasız formatta (bosluksuz) hazirla
    # separators=(',', ':') Abacus'un "list" olarak tanimasini garanti eder
    compact_json = json.dumps(payload, separators=(',', ':'))

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    try:
        # data= kullanarak ham veriyi (raw) hic degismeden gonderiyoruz
        response = requests.post(ABACUS_URL, data=compact_json.encode('utf-8'), headers=headers, timeout=60)
        
        logger.info(f"Abacus Status: {response.status_code}")
        res_json = response.json()
        
        if res_json.get("success"):
            result = res_json.get("result", {})
            raw_answer = result.get("answer") or result.get("content") or ""
            
            # --- TEMİZLİK ---
            clean = str(raw_answer)
            junk = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status"]
            for tag in junk:
                clean = clean.replace(tag, "")
            
            clean = clean.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').strip()
            return {"analysis": clean}
            
        return {"error": f"Abacus Reddi: {res_json.get('error')}"}

    except Exception as e:
        return {"error": f"Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)