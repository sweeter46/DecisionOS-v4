import os
import uvicorn
import requests
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Hata ayıklama loglarını aktif ediyoruz
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Web sitesinden gelen isteklere izin veriyoruz
app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"], 
    allow_methods=["*"], 
    allow_headers=["*"]
)

# --- SENİN ABACUS CO-PILOT AYARLARIN ---
API_KEY = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"
# ---------------------------------------

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # Abacus'a hem soruyu hem de ekranın beklediği JSON formatını gönderiyoruz
    prompt_text = f"Soru: {incident.text}. Yanıtı sadece şu JSON formatında ver: {{\"title\": \"...\", \"description\": \"...\", \"type\": \"bar\", \"table_data\": [{{ \"Key\": \"Value\" }}], \"chart_labels\": [\"A\", \"B\"], \"chart_values\": [10, 20], \"math_formula\": \"...\", \"analysis\": \"...\"}}. JSON dışında hiçbir metin yazma, açıklama yapma."

    # Abacus API URL
    url = f"https://abacus.ai/api/v0/getChatResponse?deploymentToken={API_KEY}&deploymentId={DEPLOYMENT_ID}"

    # Abacus'un kabul ettiği en kararlı mesaj yapısı
    payload = {
        "messages": [
            {
                "is_user": True,
                "text": prompt_text
            }
        ]
    }

    try:
        # JSON'ı en sıkı haliyle paketliyoruz (HTTP 400 hatasını önlemek için)
        raw_payload = json.dumps(payload, separators=(',', ':'))

        response = requests.post(
            url,
            data=raw_payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            timeout=60 # AI'nın düşünmesi için 60 saniye süre tanı
        )

        logger.info(f"Abacus Reddi: {response.status_code}")

        if response.status_code != 200:
            return {
                "title": "Sistem Meşgul", 
                "description": f"Abacus hata verdi (Kod: {response.status_code})", 
                "table_data": [{"Durum": "Başarısız"}], 
                "chart_labels": ["Error"], 
                "chart_values": [0], 
                "math_formula": "", 
                "analysis": "Lütfen API anahtarını ve Deployment ID'yi kontrol et."
            }

        res_json = response.json()
        raw_ai_text = res_json['result']['text']

        # AI'nın cevabındaki JSON bloğunu ayıklıyoruz
        json_match = re.search(r'(\{.*\})', raw_ai_text, re.DOTALL)

        if json_match:
            # Sadece JSON kısmını geri döndür
            return json.loads(json_match.group(1))
        else:
            # Eğer AI JSON veremediyse, gelen metni analiz kısmına bas
            return {
                "title": "Dinamik Bilgi Akışı", 
                "description": "AI serbest metin üretti.", 
                "table_data": [{"Bilgi": "Düz Metin"}], 
                "chart_labels": ["AI"], 
                "chart_values": [100], 
                "math_formula": "", 
                "analysis": raw_ai_text
            }

    except Exception as e:
        logger.error(f"Kritik Hata: {str(e)}")
        return {
            "title": "Bağlantı Sorunu", 
            "description": str(e), 
            "table_data": [], 
            "chart_labels": [], 
            "chart_values": [], 
            "math_formula": "", 
            "analysis": "Render veya Abacus bağlantısında bir kopma yaşandı."
        }

if __name__ == "__main__":
    # Render'ın beklediği Port ayarı
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)