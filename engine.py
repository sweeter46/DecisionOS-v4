import logging, requests, json, os, re, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    user_text = str(incident.text).strip()
    
    # EVRENSEL SİSTEM TALİMATI (28 PAKET & ÇOKLU ÇIKTI)
    system_instruction = """
    Sen DecisionOS v4.0 Prometheus çekirdeğisin. Aşağıdaki kurallara UY:
    1. Her isteği 28 uzman paket (LAW, FIN, EDU, CYBER, vb.) üzerinden analiz et.
    2. Eğer talep bir Eğitim/Sınav ise: 'action_plan' içine en az 10-15 soru yerleştir.
    3. Matematiksel formülleri mutlaka LaTeX ($$...$$) formatında yaz.
    4. Grafik/Şema istenirse Mermaid.js formatında (```mermaid ... ```) kod üret.
    5. 'final_decision', 'analysis', 'action_plan', 'veto', 'confidence' alanlarını içeren JSON döndür.
    6. 'action_plan' içindeki anahtarlar 0-1h, 1-24h, 24-72h olmalı ancak içerik zenginleştirilmeli.
    """

    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps([{"is_user": False, "text": system_instruction}, {"is_user": True, "text": user_text}])
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        ai_data = response.json()
        if ai_data.get("success"):
            raw_text = next((m.get("text", "") for m in reversed(ai_data.get("result", {}).get("messages", [])) if not m.get("is_user")), "")
            content = raw_text.strip().replace("```json", "").replace("```", "").strip()
            # JSON Temizliği
            try:
                final_obj = json.loads(content, strict=False)
                if isinstance(final_obj, str): final_obj = json.loads(final_obj, strict=False)
                return {"report": final_obj, "status": "success"}
            except:
                match = re.search(r'(\{.*\})', content, re.DOTALL)
                return {"report": json.loads(match.group(1), strict=False), "status": "success"} if match else {"report": raw_text, "status": "text"}
        return {"report": "API Fail", "status": "error"}
    except Exception as e: return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))