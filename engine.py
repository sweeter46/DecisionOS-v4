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
    # 🚨 TEST PANELİNDE ÇALIŞAN SAF JSON YAPISI
    # Safe_text içerisindeki tırnakları temizliyoruz ki JSON kırılmasın
    clean_msg = str(incident.text).replace('"', "'").replace("\n", " ")

    # Kütüphaneye (requests.json) güvenmiyoruz. 
    # Test panelindeki başarımızı bu "Ham String" (Raw String) ile Render'a taşıyoruz.
    raw_payload = (
        '{"deploymentToken":"' + DEPLOYMENT_TOKEN + '",'
        '"deploymentId":"' + DEPLOYMENT_ID + '",'
        '"messages":[{"is_user":true,"text":"' + clean_msg + '"}]}'
    )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DecisionOS-Final-Fixed/22.0"
    }

    try:
        # DATA= kullanarak python'un veriyi 'list değil objesi'ne çevirmesini engelliyoruz.
        response = requests.post(
            ABACUS_URL, 
            data=raw_payload.encode('utf-8'), 
            headers=headers, 
            timeout=60
        )
        
        logger.info(f"Abacus Log: {response.text}")
        res_json = response.json()
        
        if res_json.get("success"):
            answer = res_json.get("result", {}).get("answer", "")
            # --- TEMİZLİK ---
            clean = str(answer).replace('{', '').replace('}', '').replace('"', '').replace(':', '').strip()
            return {"analysis": clean}
            
        return {"error": f"Abacus Reddi: {res_json.get('error')}"}

    except Exception as e:
        return {"error": f"Sistem Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)