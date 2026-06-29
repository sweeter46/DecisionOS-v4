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

# --- SENİN DOĞRULANMIŞ ABACUS BİLGİLERİN ---
API_KEY = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # AI'yı bu formatta cevap vermeye zorluyoruz
    prompt = f"""
    Sen DecisionOS v4.0 çekirdeğisin. Konu: {incident.text}
    Cevabı SADECE şu JSON formatında ver, başka hiçbir açıklama ekleme:
    {{
        "title": "BAŞLIK",
        "description": "AÇIKLAMA",
        "type": "bar",
        "table_data": [{{"Parametre": "Değer"}}],
        "chart_labels": ["A", "B", "C"],
        "chart_values": [10, 20, 30],
        "math_formula": "FORMÜL",
        "analysis": "ANALİZ NOTU"
    }}
    """

    url = f"https://abacus.ai/api/v0/getChatResponse?deploymentToken={API_KEY}&deploymentId={DEPLOYMENT_ID}"
    
    # HATAYI BİTİREN KRİTİK YAPI: Abacus artık tam olarak bu sözlük yapısını bekliyor
    payload = {
        "messages": [
            {
                "is_user": True,
                "text": prompt
            }
        ]
    }

    try:
        # json= payload kullanımı bazen kütüphane farkından hata yaratabilir, 
        # bu yüzden en güvenli yol olan json.dumps kullanıyoruz.
        response = requests.post(
            url, 
            data=json.dumps(payload),
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        if response.status_code != 200:
            return {"title": "Bağlantı Hatası", "description": f"Abacus Yanıtı: {response.status_code}", "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Lütfen Abacus tarafında Deployment'ın aktifliğini kontrol et."}

        res_data = response.json()
        ai_response_text = res_data['result']['text']

        # AI bazen konuşmaya başlar ("İşte istediğin JSON:" gibi), biz sadece JSON kısmını çekiyoruz
        json_match = re.search(r'(\{.*\})', ai_response_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            # Yedek plan: Eğer AI JSON vermezse bile ekran kilitlenmesin
            return {
                "title": "SİSTEM ANALİZİ",
                "description": incident.text,
                "type": "line",
                "table_data": [{"Durum": "Canlı Akış"}],
                "chart_labels": ["Veri"],
                "chart_values": [100],
                "math_formula": "E=mc^2",
                "analysis": ai_response_text
            }

    except Exception as e:
        return {"title": "Kritik Hata", "description": str(e), "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Render/Abacus tüneli kurulamadı."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)