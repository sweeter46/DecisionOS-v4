import logging
import requests
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json, os, re, uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.get("/")
async def root():
    return {"status": "DecisionOS Backend is running"}

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    messages_list = [{"is_user": True, "text": str(incident.text).strip()}]
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps(messages_list)
    }

    try:
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
            
            # --- KRİTİK TEMİZLİK KATMANI ---
            # Eğer raw_text tırnakla çevrili bir string ise, onu gerçek objeye çevir
            content = raw_text.strip()
            
            # Markdown temizliği (Eğer varsa)
            content = content.replace("```json", "").replace("```", "").strip()
            
            try:
                # 1. Deneme: Doğrudan Parse
                final_obj = json.loads(content)
                # Eğer hâlâ bir string döndürüyorsa bir kez daha parse et (Double Encoding Fix)
                if isinstance(final_obj, str):
                    final_obj = json.loads(final_obj)
            except:
                # 2. Deneme: Regex ile içinden çek
                match = re.search(r'(\{.*\})', content, re.DOTALL)
                if match:
                    final_obj = json.loads(match.group(1))
                    if isinstance(final_obj, str):
                        final_obj = json.loads(final_obj)
                else:
                    final_obj = {"error": "JSON_NOT_FOUND", "raw": content}

            return {"report": final_obj, "status": "success"}
            
        return {"report": ai_data.get("error"), "status": "error"}

    except Exception as e:
        return {"report": f"Sunucu Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)