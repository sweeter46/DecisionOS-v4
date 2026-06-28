from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import json
import os
import uvicorn

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
    
    # PARAMETRELERİ HAZIRLA
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

    # --- KRİTİK RÖNTGEN BÖLGESİ ---
    json_data = json.dumps(payload)
    print("------------------------------------------")
    print(f"ABACUS'A GİDEN HAM VERİ: {json_data}")
    print(f"MESSAGES TİPİ: {type(payload['messages'])}")
    print("------------------------------------------")
    
    headers = {"Content-Type": "application/json"}

    try:
        # DATA= kullanarak ham string gönderiyoruz
        response = requests.post(url, data=json_data, headers=headers, timeout=60)
        ai_data = response.json()
        
        # Eğer hala hata geliyorsa tam gövdeyi logda görelim
        if not ai_data.get("success"):
            print(f"ABACUS'TAN GELEN HATA GÖVDESİ: {ai_data}")
            
        return {"report": ai_data, "status": "raw_check"}
    
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)