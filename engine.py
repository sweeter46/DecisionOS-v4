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
    
    # FORMAT D MANTIĞI: Listeyi önce bir stringe çeviriyoruz
    messages_list = [{"is_user": True, "text": str(incident.text).strip()}]
    messages_as_string = json.dumps(messages_list) # BURASI KRİTİK: Listeyi metne çevirdik
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": messages_as_string # Abacus bunu bu şekilde bekliyor
    }

    try:
        logger.info(f"Format D Paketi Gönderiliyor: {payload}")
        
        # Requests kütüphanesi json=payload yaparken messages'ı string olarak iletecek
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            result = ai_data.get("result", {})
            messages = result.get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
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