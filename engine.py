import os
import json
import requests
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ABACUS TEMEL YAPILANDIRMA
# NOT: URL'nin sonunda deploymentId zaten gömülü olabilir, bu yüzden parametre olarak yollamıyoruz.
ABACUS_URL = "https://abacus.ai/api/v0/getChatResponse"
DEPLOYMENT_TOKEN = "79782bc44" # Senin Token'ın

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        user_text = body.get("text", "")
        
        # Sadece Token yolluyoruz, hata veren 'deploymentId'yi sildik.
        payload = {
            "deploymentToken": DEPLOYMENT_TOKEN,
            "messages": [{"is_user": True, "text": user_text}]
        }
        
        headers = {"Content-Type": "application/json"}
        
        # Abacus Çağrısı
        response = requests.post(ABACUS_URL, json=payload, headers=headers)
        res_json = response.json()
        
        if not res_json.get("success"):
            return {"error": f"Abacus Reddi: {res_json.get('error')}"}

        # --- ARINDIRMA MOTORU ---
        raw_answer = res_json.get("result", {}).get("answer", "")
        
        # Eğer yanıt bir JSON string ise içinden asıl metni çekmeye çalış
        clean_text = raw_answer
        try:
            # AI bazen yanıtı tırnak içinde JSON olarak döner
            if raw_answer.strip().startswith('{'):
                parsed = json.loads(raw_answer)
                clean_text = parsed.get("report_content", raw_answer)
        except:
            pass

        # "report_content:", "status:", "confidence:" gibi kelimeleri temizle
        targets = ["report_content", "evidence_and_checklist", "veto", "confidence", "disclaimer", "status", "boot_log"]
        for target in targets:
            if target in clean_text:
                # Sadece bu kelimeleri ve yanındaki işaretleri temizle
                clean_text = clean_text.replace(target, "")

        # Kalan tırnak ve parantez temizliği
        clean_text = clean_text.replace('"', '').replace('{', '').replace('}', '').replace(':', '').strip()

        return {"analysis": clean_text}

    except Exception as e:
        logger.error(f"Hata: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)