from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn

app = FastAPI()

# Tarayıcı engelini (CORS) burada kaldırıyoruz
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
    # ABACUS TÜM PARAMETRELERİ BURADA SET EDİLİYOR
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [{"is_user": True, "text": incident.text}] # Doğru Format
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        
        if ai_data.get("success"):
            report = ai_data["result"].get("content") or ai_data["result"].get("text")
            return {"report": report}
        else:
            return {"report": f"Abacus Hatası: {ai_data.get('error')}"}
    except Exception as e:
        return {"report": f"Sunucu Hatası: {str(e)}"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)