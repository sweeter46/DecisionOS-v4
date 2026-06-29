import os
import json
import requests
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Sistem Logları (Engineering Mode)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ABACUS YAPILANDIRMASI
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"
DEPLOYMENT_TOKEN = "79782bc44" # Senin tokenın
DEPLOYMENT_ID = "1268ee5e2"     # Senin ID'n

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        user_text = body.get("text", "")
        
        payload = {
            "deploymentToken": DEPLOYMENT_TOKEN,
            "deploymentId": DEPLOYMENT_ID,
            "messages": [{"is_user": True, "text": user_text}]
        }
        
        headers = {"Content-Type": "application/json", "User-Agent": "DecisionOS-Architect/1.0"}
        
        # Abacus Çağrısı
        response = requests.post(ABACUS_URL, json=payload, headers=headers)
        res_json = response.json()
        
        if not res_json.get("success"):
            return {"error": f"Abacus Reddi: {res_json.get('error')}"}

        # --- YAZILIM USTASI MÜDAHALESİ (THE ARCHITECT) ---
        raw_ai_answer = res_json.get("result", {}).get("answer", "")
        logger.info(f"Ham AI Yanıtı: {raw_ai_answer[:100]}...")

        # AI bazen yanıtı bir string'in içine gömer. Burası onu ayıklar.
        clean_text = ""
        try:
            # Eğer yanıt bir JSON string ise içindeki report_content'i al
            parsed = json.loads(raw_ai_answer)
            clean_text = parsed.get("report_content", raw_ai_answer)
        except:
            # Eğer doğrudan metin geldiyse veya parse edilemiyorsa
            clean_text = raw_ai_answer

        # Ekstra temizlik: Başlardaki ve sondaki gereksiz teknik kırıntıları uçur
        if "report_content" in clean_text:
            clean_text = clean_text.split("report_content", 1)[-1].strip(": \"'")
        
        # Eğer hala JSON kırıntısı kaldıysa final temizlik
        clean_text = clean_text.replace('"}', '').replace('"', '').strip()

        return {"analysis": clean_text}

    except Exception as e:
        logger.error(f"Hata: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)