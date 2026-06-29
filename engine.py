import os
import uvicorn
import requests
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- LÜTFEN BURAYI DOLDUR ---
API_KEY = "sk_..."  # Senin Deployment Token'ın
DEPLOYMENT_ID = "..."  # Senin Deployment ID'n
# ----------------------------

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # Abacus'un istediği mutlak prompt ve format
    prompt_text = f"Soru: {incident.text}. Yanıtı sadece şu JSON formatında ver: {{\"title\": \"...\", \"description\": \"...\", \"type\": \"bar\", \"table_data\": [{{ \"Key\": \"Value\" }}], \"chart_labels\": [\"A\", \"B\"], \"chart_values\": [10, 20], \"math_formula\": \"...\", \"analysis\": \"...\"}}. JSON dışında tek kelime yazma."

    # Abacus URL
    url = f"https://abacus.ai/api/v0/getChatResponse?deploymentToken={API_KEY}&deploymentId={DEPLOYMENT_ID}"
    
    # PARAMETRE HATASINI ÖNLEYEN SAF PAYLOAD
    payload = {
        "messages": [
            {
                "is_user": True, 
                "text": prompt_text
            }
        ]
    }

    try:
        # JSON'ı en sıkı haliyle (boşluksuz) serialize ediyoruz
        raw_payload = json.dumps(payload, separators=(',', ':'))
        
        response = requests.post(
            url, 
            data=raw_payload.encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            timeout=60
        )
        
        logger.info(f"Abacus Status: {response.status_code}")
        
        if response.status_code != 200:
            return {"title": "Sistem Meşgul", "description": f"Abacus hata verdi (Kod: {response.status_code})", "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Lütfen API anahtarlarını kontrol et."}

        res_json = response.json()
        raw_ai_text = res_json['result']['text']
        
        # AI'nın cevabındaki JSON bloğunu ayıkla
        json_match = re.search(r'(\{.*\})', raw_ai_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            return {"title": "Zeka Formatı Sapması", "description": "AI serbest metin üretti.", "table_data": [{"Metin": "Alınan Yanıt"}], "chart_labels": ["AI"], "chart_values": [100], "math_formula": "", "analysis": raw_ai_text[:200]}

    except Exception as e:
        logger.error(f"Hata: {str(e)}")
        return {"title": "Bağlantı Sorunu", "description": str(e), "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Render/Abacus arası kopukluk."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)