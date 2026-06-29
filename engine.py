import os
import json
import logging
import urllib.request
import urllib.error
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

# KREDİLER
DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    # MESAJI HAZIRLA
    safe_text = str(incident.text).replace('"', "'").replace("\n", " ").strip()
    
    # MANUEL JSON (Urllib için en saf haliyle)
    payload_dict = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [
            {
                "is_user": True,
                "text": safe_text
            }
        ]
    }
    
    # JSON'I BYTE'A ÇEVİR (Requests kütüphanesi olmadan)
    binary_data = json.dumps(payload_dict).encode('utf-8')
    
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DecisionOS-Nuclear-V19/1.0"
    }

    try:
        # URLLIB İLE SAF TRANSFER
        req = urllib.request.Request(ABACUS_URL, data=binary_data, headers=headers, method='POST')
        
        with urllib.request.urlopen(req) as f:
            response_data = f.read().decode('utf-8')
            res_json = json.loads(response_data)
            
        if res_json.get("success"):
            raw_answer = res_json.get("result", {}).get("answer", "")
            
            # --- PROFESYONEL TEMİZLİK ---
            clean = raw_answer
            junk = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial"]
            for tag in junk:
                clean = clean.replace(tag, "")
            
            clean = clean.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').replace('\\', '').replace(':', '').strip()
            return {"analysis": clean}
            
        return {"error": f"Abacus Reddi: {res_json.get('error')}"}

    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": f"HTTP Hatası: {e.code} - {error_body}"}
    except Exception as e:
        return {"error": f"Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)