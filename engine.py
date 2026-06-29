import os
import json
import requests
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ABACUS KİMLİK BİLGİLERİ
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"
DEPLOYMENT_TOKEN = "79782bc44"
DEPLOYMENT_ID = "1268ee5e2" # Senin sistemindeki ID

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        user_text = body.get("text", "")
        
        # Abacus'un tam olarak beklediği yapı
        payload = {
            "deploymentToken": DEPLOYMENT_TOKEN,
            "deploymentId": DEPLOYMENT_ID, # Hem ID hem Token bir arada
            "messages": [{"is_user": True, "text": user_text}]
        }
        
        headers = {"Content-Type": "application/json"}
        
        # İstek Gönderimi
        response = requests.post(ABACUS_URL, json=payload, headers=headers)
        res_json = response.json()
        
        # Ham yanıtı logla (sorunu terminalden görmek için)
        logger.info(f"Abacus Yanıtı: {res_json}")

        if not res_json.get("success"):
            return {"error": f"Abacus Reddi: {res_json.get('error')}"}

        # --- ARINDIRMA MOTORU ---
        raw_answer = res_json.get("result", {}).get("answer", "")
        
        # Gelen veriyi temizle
        clean_text = raw_answer
        # Teknik kelimeleri temizle
        junk = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial"]
        for word in junk:
            clean_text = clean_text.replace(word, "")
        
        # Tırnak ve parantez temizliği
        clean_text = clean_text.replace('"', '').replace('{', '').replace('}', '').replace(':', '').strip()

        return {"analysis": clean_text}

    except Exception as e:
        logger.error(f"Sistem Hatası: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)