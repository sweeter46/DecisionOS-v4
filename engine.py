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

    # AI'yı ham veri üretmeye zorlayan "Ultimate Strict Instruction"
    # Tablo ve Grafiklerin ayrı satırlarda olması gerektiğini vurguluyoruz.
    system_instruction = """
    Sen DecisionOS v4.0 Prometheus çekirdeğisin. 
    ZORUNLU ÇIKTI KURALLARI:
    1. SADECE JSON DÖNDÜR.
    2. TABLO: Tablo verisi istendiğinde, onu mutlaka AŞAĞIDAKİ GİBİ AYRI BİR PARAGRAF olarak Markdown formatında yolla:

       | Başlık | Değer |
       | :--- | :--- |
       | Örnek | 100 |

    3. GRAFİK: Grafik istendiğinde, mutlaka ```chart {JSON_CONFIG} ``` kod bloğunu 'analysis' veya 'action_plan' içinde AYRI BİR SATIRDA yolla.
    4. LaTeX formülleri için $$ ... $$ kullan ve başına/sonuna boş satır koy.

    JSON Şeması:
    {
      "final_decision": "string",
      "analysis": "string",
      "action_plan": {"0-1h": [], "1-24h": [], "24-72h": []},
      "confidence": 0.0,
      "veto": "string or null"
    }
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

            # --- GELMİŞ GEÇMİŞ EN GÜÇLÜ JSON TEMİZLEME ALGORİTMASI ---
            content = raw_text.strip()
            # Markdown kod bloklarını (json) temizle
            content = content.replace("```json", "").replace("```JSON", "").replace("```", "")

            try:
                # 1. Direkt temizlemiş içeriği dene
                final_obj = json.loads(content.strip(), strict=False)
                return {"report": final_obj, "status": "success"}
            except:
                # 2. Regex ile en dıştaki {} objesini yakala
                match = re.search(r'(\{[\s\S]*\})', content)
                if match:
                    try:
                        clean_json = match.group(1).replace('\n', ' ').replace('\r', '')
                        parsed = json.loads(clean_json, strict=False)
                        return {"report": parsed, "status": "success"}
                    except:
                        pass

                # 3. Fail-Safe: Bozuk veriyi "analysis" içine gömerek döndür
                return {
                    "report": {
                        "final_decision": "DATA_RECOVERY_MODE", 
                        "analysis": raw_text,
                        "action_plan": {"0-1h": ["Veri formatı uyumsuzluğu saptandı."], "1-24h": [], "24-72h": []},
                        "confidence": 0.3
                    }, 
                    "status": "partial"
                }

        return {"report": "Abacus Sync Error", "status": "error"}
    except Exception as e:
        logger.error(f"Sunucu Hatası: {str(e)}")
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    # Render'ın beklediği port ayarı
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)