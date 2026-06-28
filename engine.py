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
    
    # ABACUS'UN AZ ÖNCE HATA MESAJINDA İSTEDİĞİ KESİN FORMAT 
    # (is_user anahtarı küçük harf 'true' olacak şekilde JSON'a zorlanıyor)
    # text içindeki tırnak işaretlerini temizleyerek listenin yapısını koruyoruz.
    safe_text = str(incident.text).replace('"', "'").replace("\n", " ").strip()
    
    # Paketi manuel olarak (String Injection ile) en saf haliyle inşa ediyoruz.
    # Bu yöntem, listenin internetten geçerken bozulma şansını sıfıra indirir.
    payload_str = (
        '{'
        f'"deploymentToken": "f3baa2a32be542f9af98a81aa71da611",'
        f'"deploymentId": "63a2ddb70",'
        f'"messages": [{{ "is_user": true, "text": "{safe_text}" }}]'
        '}'
    )

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        logger.info(f"MÜHÜRLÜ PAKET GÖNDERİLİYOR: {payload_str}")
        
        # data= kullanarak ham stringi doğrudan Abacus'un kapısına bırakıyoruz
        response = requests.post(url, data=payload_str.encode('utf-8'), headers=headers, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            result = ai_data.get("result", {})
            messages_out = result.get("messages", [])
            raw_text = ""
            
            # AI'dan gelen en son mesajı çekiyoruz
            for m in reversed(messages_out):
                if not m.get("is_user"):
                    raw_text = m.get("text", "")
                    break
            
            # Dashboard JSON ayıklama
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try: 
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except: 
                    pass
            
            return {"report": raw_text, "status": "text"}
            
        return {"report": f"Abacus Reddi: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Sistem Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)