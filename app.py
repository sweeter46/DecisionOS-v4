from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests, os, uvicorn, json, re

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": [{"is_user": True, "text": incident.text}]
    }
    try:
        r = requests.post(url, json=payload, timeout=45).json()
        if r.get("success"):
            # En son gelen mesajı bul
            text = [m.get("text", "") for m in r["result"]["messages"] if not m.get("is_user")][-1]
            # JSON Ayıkla
            match = re.search(r'(\{.*\})', text.replace("```json", "").replace("```", ""), re.DOTALL)
            if match:
                return {"report": json.loads(match.group(1)), "status": "success"}
            return {"report": text, "status": "text"}
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))