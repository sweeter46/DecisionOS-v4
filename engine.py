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

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    user_text = str(incident.text).strip()
    
    # --- EĞİTİM MODU TESPİTİ ---
    is_edu = any(x in user_text.lower() for x in ["ders", "eğitim", "kpss", "sınav", "üniversite", "notu"])
    
    # Eğer eğitim isteğiyse uzmanlık setini değiştiriyoruz
    system_instruction = """
    Sen DecisionOS v4.0 Prometheus çekirdeğisin. 
    Eğer talep bir eğitim/ders notu ise: 
    1) 'final_decision' alanına ünitenin tam adını yaz. 
    2) 'analysis' alanına konuyu KPSS/Akademik ciddiyette, teknik detaylarla açıkla. 
    3) 'action_plan' içindeki '0-1h' listesine en kritik 5 teknik maddeyi yaz. 
    4) 'action_plan' içindeki '1-24h' listesine 3 adet zorluk seviyesi yüksek (KPSS dengi) çoktan seçmeli soru ve cevap anahtarını yaz.
    Cevabı mutlaka JSON formatında döndür.
    """

    messages_list = [
        {"is_user": False, "text": system_instruction},
        {"is_user": True, "text": user_text}
    ]
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps(messages_list)
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            messages = ai_data.get("result", {}).get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")
            
            # Temizlik ve JSON Parse
            content = raw_text.strip().replace("```json", "").replace("```", "").strip()
            try:
                final_obj = json.loads(content, strict=False)
                if isinstance(final_obj, str): final_obj = json.loads(final_obj, strict=False)
                return {"report": final_obj, "status": "success"}
            except:
                # Regex Fallback
                match = re.search(r'(\{.*\})', content, re.DOTALL)
                if match:
                    return {"report": json.loads(match.group(1), strict=False), "status": "success"}
                return {"report": raw_text, "status": "text"}
            
        return {"report": "API Hatası", "status": "error"}
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))