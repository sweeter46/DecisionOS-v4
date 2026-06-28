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

@app.get("/")
async def root():
    return {"status": "DecisionOS Backend is running"}

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    messages_list = [{"is_user": True, "text": str(incident.text).strip()}]
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps(messages_list)
    }

    try:
        response = requests.post(url, json=payload, timeout=60)
        ai_data = response.json()
        
        if ai_data.get("success"):
            result = ai_data.get("result", {})
            messages = result.get("messages", [])
            raw_text = next((m.get("text", "") for m in reversed(messages) if not m.get("is_user")), "")
            
            # --- GELİŞMİŞ TEMİZLİK (STRICT=FALSE) ---
            content = raw_text.strip()
            content = content.replace("```json", "").replace("```", "").strip()

            # Eğer tırnakla paketlenmişse (Stringified JSON), tırnakları ve kaçışları temizle
            if content.startswith('"') and content.endsWith('"'):
                try: 
                    # Bu satır, string içindeki \" ve \n gibi kaçış karakterlerini çözer
                    content = json.loads(content)
                except: 
                    content = content[1:-1]

            def smart_parse(text):
                try:
                    # strict=False gizli kontrol karakterlerini (tab, newline vb.) görmezden gelir
                    return json.loads(text, strict=False)
                except:
                    # Regex ile süslü parantez içine odaklan
                    match = re.search(r'(\{.*\})', text, re.DOTALL)
                    if match:
                        return json.loads(match.group(1), strict=False)
                    raise ValueError("JSON Yapısı Bulunamadı")

            try:
                final_obj = smart_parse(content)
                # Double encoding kontrolü
                if isinstance(final_obj, str):
                    final_obj = smart_parse(final_obj)
                
                return {"report": final_obj, "status": "success"}
            except Exception as e:
                logger.error(f"Parse Hatası: {str(e)} | İçerik: {content[:100]}")
                return {"report": raw_text, "status": "text"} # Hata olsa bile ham metni yolla, HTML parse eder
            
        return {"report": ai_data.get("error"), "status": "error"}

    except Exception as e:
        return {"report": f"Sistem Hatası: {str(e)}", "status": "error"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)