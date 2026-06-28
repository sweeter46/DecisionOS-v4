import logging, requests, json, os, re, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("decisionos")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # AI'yı KOD yazmaya zorlamak için "DOĞRU ÖRNEK" (Few-Shot) ekledik
    system_instruction = """
    Sen DecisionOS Prometheus çekirdeğisin. Sadece JSON formatında, asla açıklama yapmadan cevap ver.
    
    ZORUNLU FORMAT ÖRNEĞİ (analysis alanı içinde grafik kodu olmalı):
    {
      "final_decision": "YAP",
      "analysis": "Veriler analiz edildi. ```chart { 'type': 'line', 'data': { 'labels': ['Oca','Sub'], 'datasets': [{ 'label': 'Test', 'data': [10, 20], 'borderColor': '#6366f1' }] } } ```",
      "action_plan": {"0-1h": ["Tabloyu oluştur"], "1-24h": [], "24-72h": []},
      "confidence": 0.98
    }
    
    Eğer kullanıcı 'enflasyon' veya 'grafik' derse, yukarıdaki ```chart ... ``` bloğunu GERÇEK VERİLERLE mutlaka üret.
    """

    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps([
            {"is_user": False, "text": system_instruction}, 
            {"is_user": True, "text": f"GÖREV: {incident.text}. Mutlaka grafik kodunu (```chart) ve tabloyu (Markdown) analysis içine ekle!"}
        ])
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data.get("result", {}).get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")
            
            # JSON Ayıklama
            match = re.search(r'(\{[\s\S]*\})', raw_text)
            if match:
                try:
                    parsed = json.loads(match.group(1), strict=False)
                    return {"report": parsed, "status": "success"}
                except: pass
            
            return {"report": {"final_decision": "RECOVERY", "analysis": raw_text, "action_plan": {"0-1h": []}, "confidence": 0.5}, "status": "partial"}
            
        return {"report": "API_ERROR", "status": "error"}
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))