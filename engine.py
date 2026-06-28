import logging
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, re, uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"

    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "is_user": True,
                "text": incident.text.strip()
            }
        ]
    }

    # ✅ DÜZELTME: data= yerine json= kullan
    # requests kütüphanesi json= parametresiyle otomatik olarak:
    # 1) Content-Type: application/json header'ı ekler
    # 2) Veriyi doğru JSON formatında gönderir
    # 3) messages listesini bozMaz
    try:
        logger.info(f"GÖNDERİLEN PAYLOAD: {json.dumps(payload, ensure_ascii=False)}")

        response = requests.post(
            url,
            json=payload,          # ← SADECE BU DEĞİŞTİ
            timeout=60
        )

        logger.info(f"HTTP DURUM KODU: {response.status_code}")
        logger.info(f"HAM YANIT: {response.text[:500]}")

        ai_data = response.json()

        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break

            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)

            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except json.JSONDecodeError:
                    pass

            return {"report": raw_text, "status": "text"}

        return {"report": f"Abacus Reddi: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        logger.error(f"HATA: {str(e)}")
        return {"report": f"Bağlantı Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)