import logging
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, re, uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # ABACUS'UN İSTEDİĞİ KESİN ŞEMA
    # 'is_user' anahtarının Python'da True (Boolean) olduğundan eminiz.
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

    # VERİYİ RAW JSON STRING OLARAK MÜHÜRLE
    # separators=(',', ':') kullanarak gereksiz boşlukları siliyoruz (Abacus bunu sever)
    raw_payload_data = json.dumps(payload, separators=(',', ':'))

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        logger.info(f"MÜHÜRLÜ GÖNDERİ: {raw_payload_data}")
        
        # data= kullanarak ham stringi gönderiyoruz
        response = requests.post(url, data=raw_payload_data.encode('utf-8'), headers=headers, timeout=60)
        
        if response.status_code != 200:
            # Hata devam ederse alternatif 'llmInput' formatına anlık geçiş
            logger.warning("Varyant 1 başarısız, Varyant 2 (llmInput) deneniyor...")
            alt_payload = {
                "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
                "deploymentId": "63a2ddb70",
                "llmInput": str(incident.text).strip()
            }
            response = requests.post(url, data=json.dumps(alt_payload).encode('utf-8'), headers=headers, timeout=60)

        ai_data = response.json()
        
        if ai_data.get("success"):
            result = ai_data.get("result", {})
            # Yanıt formatına göre metni ayıkla
            if isinstance(result, str):
                raw_text = result
            else:
                messages = result.get("messages", [])
                raw_text = messages[-1].get("text", "") if messages else str(result)
            
            # Dashboard JSON ayıklama
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try: return {"report": json.loads(match.group(1)), "status": "success"}
                except: pass
            
            return {"report": raw_text, "status": "text"}
            
        return {"report": f"Abacus Reddi: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Bağlantı Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)