import logging
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, re, uvicorn

# Render loglarında hatayı canlı görmek için loglama
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # ABACUS'UN İSTEDİĞİ KESİN ŞABLON (is_user: True, text: str)
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "is_user": True,
                "text": str(incident.text).strip()
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Log: Abacus'a tam olarak ne gönderiyoruz?
        logger.info(f"Abacus'a paket gönderiliyor: {json.dumps(payload)}")
        
        # 'json=' parametresi listeyi doğrudan JSON array'ine dönüştürür (Kritik nokta)
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"HATA ALINDI: HTTP {response.status_code} - Yanıt: {response.text}")
            return {"report": f"Abacus Reddi (HTTP {response.status_code}): {response.text}", "status": "error"}

        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            # Dashboard JSON ayıklama mantığı
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except: pass
            
            return {"report": raw_text, "status": "text"}
            
        return {"report": f"Abacus Hatası: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        logger.exception("Bağlantı sırasında beklenmedik hata!")
        return {"report": f"Bağlantı Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)