import os
import requests
import json
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Sistem Logları
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# CORS Ayarları (Frontend bağlantısı için)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

# --- GÜNCEL ABACUS KİMLİKLERİ ---
DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"

@app.post("/analyze")
async def analyze(incident: Incident):
    try:
        # 🛡️ KRİTİK: KULLANICI MESAJINI TEMİZLE
        # Mesajın içindeki tırnaklar JSON yapısını bozmasın diye temizliyoruz
        safe_text = str(incident.text).replace('"', "'").replace("\n", " ").strip()

        # 🏗️ %100 MANUEL JSON İNŞASI
        # Artık kütüphanelerin paketleme hatasına izin yok.
        # "messages" kısmını manuel olarak [ ] içine aldık.
        raw_payload = (
            '{'
            f'"deploymentToken": "{DEPLOYMENT_TOKEN}",'
            f'"deploymentId": "{DEPLOYMENT_ID}",'
            '"messages": ['
            '  {'
            '    "is_user": true,'
            f'    "text": "{safe_text}"'
            '  }'
            ']'
            '}'
        )

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "DecisionOS-Hardcore-Architect/18.0"
        }

        # 🚀 İSTEĞİ BYTE SEVİYESİNDE GÖNDER
        response = requests.post(
            ABACUS_URL, 
            data=raw_payload.encode('utf-8'), 
            headers=headers, 
            timeout=60
        )
        
        logger.info(f"Abacus Status Code: {response.status_code}")
        ai_data = response.json()
        
        if ai_data.get("success"):
            # Modelin verdiği asıl yanıtı al
            raw_answer = ai_data.get("result", {}).get("answer", "")
            
            # --- ARINDIRMA MOTORU ---
            clean = raw_answer
            
            # report_content alanını ayıkla (varsa)
            if "report_content" in clean:
                try:
                    clean = clean.split("report_content", 1)[-1]
                except:
                    pass
            
            # Teknik etiketleri temizle
            junk_tags = ["evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "partial", "boot_log"]
            for tag in junk_tags:
                clean = clean.replace(tag, "")
            
            # Final Karakter Temizliği
            clean = clean.replace('"', '').replace('{', '').replace('}', '').replace('\\n', '\n').replace('\\', '').replace(':', '').strip()
            
            return {"analysis": clean}
            
        return {"error": f"Abacus Hatası: {ai_data.get('error')}"}

    except Exception as e:
        logger.error(f"Sistem Hatası: {str(e)}")
        return {"error": f"Sistem Bağlantı Hatası: {str(e)}"}

if __name__ == "__main__":
    # Render için dinamik PORT ayarı
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)