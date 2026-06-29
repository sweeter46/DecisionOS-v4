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

# KREDİLER
DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    # ABACUS'UN EN ÇOK KABUL ETTİĞİ 2 FARKLI YAPI
    # 1. YAPI: Standart Liste yapısı (Ama requests ile değil, en saf haliyle)
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [
            {"is_user": True, "text": str(incident.text)}
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "DecisionOS-V20/1.0"
    }

    try:
        # İLK DENEME: Standart Yapı
        response = requests.post(ABACUS_URL, json=payload, headers=headers, timeout=60)
        res_json = response.json()
        
        # EĞER YİNE "LIST" HATASI VERİRSE, OTOMATİK 2. YAPIYA GEÇ
        if not res_json.get("success") and "must be a list" in str(res_json.get("error", "")):
            logger.info("Liste hatası algılandı, alternatif yapı (Prompt Mode) deneniyor...")
            
            # 2. YAPI: Bazı Abacus sürümleri 'prompt' veya tekil 'message' bekler
            alt_payload = {
                "deploymentToken": DEPLOYMENT_TOKEN,
                "deploymentId": DEPLOYMENT_ID,
                "prompt": str(incident.text) # Liste yerine direkt string
            }
            response = requests.post(ABACUS_URL, json=alt_payload, headers=headers, timeout=60)
            res_json = response.json()

        if res_json.get("success"):
            # Yanıtı ayıkla (answer veya content alanından)
            result = res_json.get("result", {})
            raw_answer = result.get("answer") or result.get("content") or ""
            
            # --- TEMİZLİK ---
            clean = str(raw_answer)
            junk = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial"]
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