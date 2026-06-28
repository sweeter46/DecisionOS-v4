from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json
import re

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
    # Senin getirdiğin analizdeki OpenAI uyumlu endpoint ve formatı deniyoruz
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # KESİN LİSTE YAPISI VE STANDART ROLE/CONTENT FORMATI
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "role": "user",
                "content": str(incident.text)
            }
        ]
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer f3baa2a32be542f9af98a81aa71da611" # Token'ı hem içerde hem başlıkta gönderiyoruz
    }

    try:
        # json=payload yerine manuel data=json.dumps kullanımı (Bypass yöntemi)
        response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data["result"].get("messages", [])
            raw_text = ""
            for m in reversed(messages):
                # Hem 'content' hem 'text' hem 'is_user' kontrolüyle yanıtı bul
                if not m.get("is_user") or m.get("role") == "assistant":
                    raw_text = m.get("content") or m.get("text") or ""
                    break
            
            # JSON Ayıklama
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except:
                    pass
            
            return {"report": raw_text, "status": "text"}
        
        # Abacus'un hata detayını yakalayalım
        error_msg = ai_data.get('error', 'Bilinmeyen Hata')
        return {"report": f"Abacus Hatası: {error_msg}", "status": "error"}
    except Exception as e:
        return {"report": f"Sistem hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)