from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
import uvicorn
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
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # PARAMETRELERİ EN SAF HALİYLE OLUŞTUR
    # messages kısmının kesinlikle bir LİSTE [] olduğunu Abacus'a hissettiriyoruz.
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [
            {
                "is_user": True,
                "text": str(incident.text)
            }
        ]
    }

    try:
        # json.dumps kullanarak Python listesini standart JSON Array'e çeviriyoruz
        # ensure_ascii=False Türkçe karakterlerin bozulmasını engeller
        json_payload = json.dumps(payload, ensure_ascii=False)
        
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # requests.post içinde data= kancasını kullanarak HAM JSON gönderiyoruz
        response = requests.post(url, data=json_payload.encode('utf-8'), headers=headers, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            # Yanıtı çözümle
            res_obj = ai_data.get("result", {})
            messages = res_obj.get("messages", [])
            output_text = ""
            
            if messages:
                for m in reversed(messages):
                    if not m.get("is_user"):
                        output_text = m.get("text", "")
                        break
            
            # Dashboard JSON ayıkla
            clean = output_text.replace("```json", "").replace("```", "").strip()
            match = re.search(r'(\{.*\})', clean, re.DOTALL)
            
            if match:
                try:
                    return {"report": json.loads(match.group(1)), "status": "success"}
                except:
                    pass
            
            return {"report": output_text, "status": "text"}
        
        # Abacus'tan gelen hatayı ekrana bas
        return {"report": f"Abacus Reddi: {ai_data.get('error')}", "status": "error"}

    except Exception as e:
        return {"report": f"Sistem hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)