import os
import uvicorn
import requests
import json
import re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ABACUS AYARLARI (Senin Bilgilerin)
API_KEY = "sk_..." # Senin Abacus API Key'in
DEPLOYMENT_ID = "..." # Senin Deployment ID'n

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = f"https://abacus.ai/api/v0/getChatResponse?deploymentToken={API_KEY}&deploymentId={DEPLOYMENT_ID}"
    
    # Abacus'a gönderilecek prompt - Formatı zorluyoruz
    prompt = f"""
    Soru: {incident.text}
    Cevabı mutlaka şu JSON formatında ver:
    {{
        "title": "Konu Başlığı",
        "description": "Kısa açıklama",
        "type": "bar veya line veya radar",
        "table_data": [{{"anahtar": "deger"}}, ...],
        "chart_labels": ["label1", ...],
        "chart_values": [sayı1, ...],
        "math_formula": "LaTeX formülü",
        "analysis": "Eğitsel kısa özet"
    }}
    JSON dışında hiçbir metin yazma.
    """

    payload = {"messages": [{"is_user": True, "text": prompt}]}
    
    try:
        response = requests.post(url, json=payload)
        res_json = response.json()
        
        # Abacus'tan gelen metni ayıkla
        raw_content = res_json['result']['text']
        # JSON bloğunu bul (Markdown temizleme)
        json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
        if json_match:
            final_data = json.loads(json_match.group())
            return final_data
        else:
            return {"title": "Hata", "description": "AI uygun formatta cevap vermedi."}
            
    except Exception as e:
        return {"title": "Bağlantı Hatası", "description": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)