import os, uvicorn, requests, json, re
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- DOĞRULUĞUNDAN EMİN OLALIM ---
API_KEY = "f3baa2a32be542f9af98a81aa71da611"
DEPLOYMENT_ID = "63a2ddb70"

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # Promptu hazırlıyoruz
    p = f"Soru: {incident.text}. Yanıtı sadece şu JSON formatında ver: {{\"title\": \"...\", \"description\": \"...\", \"type\": \"bar\", \"table_data\": [{{ \"Key\": \"Value\" }}], \"chart_labels\": [\"A\"], \"chart_values\": [10], \"math_formula\": \"...\", \"analysis\": \"...\"}}"
    
    url = f"https://abacus.ai/api/v0/getChatResponse"
    
    # PARAMETRELERİ URL'E GÖMEREK (QUERY STRING) DENİYORUZ - EN GARANTİ YÖNTEM
    params = {
        "deploymentToken": API_KEY,
        "deploymentId": DEPLOYMENT_ID,
        "messages": json.dumps([{"is_user": True, "text": p}])
    }

    try:
        # POST isteğini params ile gönderiyoruz
        response = requests.post(url, params=params, timeout=60)
        
        if response.status_code != 200:
            return {"title": "Bağlantı Reddedildi", "description": f"Abacus (Kod: {response.status_code})", "table_data": [{"Hata": "400/401"}], "chart_labels": ["X"], "chart_values": [0], "math_formula": "", "analysis": "Lütfen Abacus'ta Deployment'ın 'Active' olduğundan emin ol."}

        res_json = response.json()
        raw_ai_text = res_json['result']['text']
        json_match = re.search(r'(\{.*\})', raw_ai_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            return {"title": "Analiz", "description": "Özet", "table_data": [], "chart_labels": ["AI"], "chart_values": [100], "math_formula": "", "analysis": raw_ai_text}

    except Exception as e:
        return {"title": "Hata", "description": str(e), "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Hata."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))