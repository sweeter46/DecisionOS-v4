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
    
    # AI'yı grafik KODUNU analysis içine yazmaya zorluyoruz
    system_instruction = """
    Sen DecisionOS Prometheus çekirdeğisin. 
    KURAL: Sadece JSON döndür.
    ZORUNLU: Tabloyu ve Grafiği (```chart {JSON} ```) mutlaka 'analysis' alanı içerisinde metinle birlikte gönder. 
    JSON Şeması:
    {
      "final_decision": "string",
      "analysis": "Buraya metin + Tablo + ```chart ... ``` bloğu gelecek",
      "action_plan": {"0-1h": [], "1-24h": [], "24-72h": []},
      "confidence": 0.95
    }
    """

    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps([{"is_user": False, "text": system_instruction}, {"is_user": True, "text": incident.text}])
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data.get("result", {}).get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")
            
            # --- JSON KURTARMA OPERASYONU ---
            # 1. En dıştaki { } bloğunu bul
            match = re.search(r'(\{[\s\S]*\})', raw_text)
            if match:
                clean_json = match.group(1)
                # 2. Tehlikeli karakterleri daha güvenli bir şekilde temizle
                # JSON içinde gerçek yeni satır karakterlerini (\n) korumalıyız yoksa tablo bozulur
                try:
                    # Strict=False parametresi kritik: Kontrol karakterlerine izin verir
                    parsed = json.loads(clean_json, strict=False)
                    return {"report": parsed, "status": "success"}
                except Exception as e:
                    logger.error(f"JSON Parse Hatası: {e}")
            
            # 3. Fail-Safe: Bozuksa ham metni ver ama recovery başlığıyla
            return {"report": {"final_decision": "RECOVERY", "analysis": raw_text, "action_plan": {"0-1h": []}, "confidence": 0.5}, "status": "partial"}
            
        return {"report": "API_ERROR", "status": "error"}
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))