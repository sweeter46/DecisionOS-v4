import logging, requests, json, os, re, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Loglama Ayarları
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

    system_instruction = """
    Sen DecisionOS v4.0 Prometheus çekirdeğisin. 
    LÜTFEN SADECE VE SADECE JSON FORMATINDA CEVAP VER. Cevabın başına veya sonuna açıklama ekleme.
    {
      "final_decision": "string",
      "analysis": "string",
      "action_plan": {"0-1h": [], "1-24h": [], "24-72h": []},
      "confidence": 0.0,
      "veto": null,
      "disclaimer": "string"
    }
    LaTeX formülleri için $$ ... $$, şemalar için ```mermaid kodlarını kullan.
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
            messages = ai_data.get("result", {}).get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")

            # --- JSON AYIKLAMA VE TEMİZLEME MOTORU ---
            content = raw_text.strip().replace("```json", "").replace("```", "").strip()

            try:
                # İlk deneme: Direkt Parse
                final_obj = json.loads(content, strict=False)
                return {"report": final_obj, "status": "success"}
            except:
                # İkinci deneme: Regex ile { } arasını bul
                match = re.search(r'(\{[\s\S]*\})', content)
                if match:
                    try:
                        clean_json = match.group(1)
                        # Geçersiz karakterleri temizle
                        clean_json = clean_json.replace('\n', ' ').replace('\r', '')
                        parsed = json.loads(clean_json, strict=False)
                        return {"report": parsed, "status": "success"}
                    except:
                        pass

                # Başarısızlık: Ham metni bir JSON yapısına sok
                return {
                    "report": {
                        "final_decision": "RAW_OUTPUT", 
                        "analysis": raw_text,
                        "action_plan": {"0-1h": ["Parse Hatası Oluştu"], "1-24h": [], "24-72h": []},
                        "confidence": 0.5
                    }, 
                    "status": "partial_fail"
                }
        return {"report": "Abacus API Hatası", "status": "error"}
    except Exception as e:
        return {"report": f"Sunucu Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))