import logging, requests, json, os, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # AI'yı JSON formatına ZORLAMIYORUZ. Rahat bırakıyoruz ki tabloyu düzgün yazsın.
    system_instruction = """
    Sen DecisionOS Prometheus çekirdeğisin. 
    Analizini şu başlıklarla düz metin olarak yap:
    [DECISION] (Kısa karar)
    [ANALYSIS] (Grafik kodu, Tablo ve LaTeX buraya gelsin)
    [PLAN] (0-1h, 1-24h görevleri)
    """

    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps([{"is_user": False, "text": system_instruction}, {"is_user": True, "text": incident.text}])
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        ai_data = response.json()
        raw_text = next((m.get("text", "") for m in reversed(ai_data["result"]["messages"]) if not m.get("is_user")), "")

        # AI'dan gelen düz metni biz JSON paketine dönüştürüyoruz
        return {
            "report": {
                "final_decision": "ANALİZ TAMAMLANDI",
                "analysis": raw_text,
                "action_plan": {"0-1h": ["Metin bazlı analiz üretildi."], "1-24h": [], "24-72h": []},
                "confidence": 0.95
            },
            "status": "success"
        }
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))