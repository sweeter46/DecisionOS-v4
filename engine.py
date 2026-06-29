import os
import requests
import json
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Usta Log Sistemi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ABACUS KİMLİĞİ (En Sade Haliyle)
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"
DEPLOYMENT_TOKEN = "79782bc44"

@app.post("/analyze")
async def analyze(request: Request):
    try:
        data = await request.json()
        user_text = data.get("text", "")

        # ARCHITECT NOTU: Bazı Abacus endpointleri deploymentId'yi JSON içinde kabul etmez.
        # Bu yüzden en temel (basic) payload yapısına dönüyoruz.
        payload = {
            "deploymentToken": DEPLOYMENT_TOKEN,
            "messages": [{"is_user": True, "text": user_text}]
        }
        
        headers = {"Content-Type": "application/json"}
        
        # İstek Gönderimi
        response = requests.post(ABACUS_URL, json=payload, headers=headers)
        res_json = response.json()
        
        logger.info(f"Abacus Raw Response: {res_json}")

        if not res_json.get("success"):
            # Eğer 'deploymentId' hatası alıyorsak, otomatik olarak alternatif yapıya geç
            error_msg = res_json.get("error", "")
            return {"error": f"Abacus Reddi: {error_msg}"}

        # --- USTA İŞİ METİN TEMİZLEME ---
        raw_answer = res_json.get("result", {}).get("answer", "")
        
        # Metni tüm teknik çöplerden (veto, confidence vb.) arındır
        clean_text = raw_answer
        
        # AI bazen yanıtı bir JSON objesi gibi fırlatır, onu yakala
        if clean_text.strip().startswith('{'):
            try:
                parsed = json.loads(clean_text)
                clean_text = parsed.get("report_content", clean_text)
            except:
                pass

        # Geleneksel temizlik (Filtreleme)
        junk_tags = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial", "boot_log"]
        for tag in junk_tags:
            clean_text = clean_text.replace(tag, "")

        # Karakter temizliği
        clean_text = clean_text.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').replace('\\', '').replace(':', '').strip()

        return {"analysis": clean_text}

    except Exception as e:
        logger.error(f"Sistem Hatası: {str(e)}")
        return {"error": "Sistem şu an meşgul, lütfen tekrar deneyin."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)