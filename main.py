from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn

app = FastAPI()

# CORS Ayarları: Sayfanın sunucuyla konuşmasına izin verir
# main.py içindeki CORS ayarını tamamen bununla değiştir:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Tüm dünyadan gelen isteklere izin ver
    allow_credentials=True,
    allow_methods=["*"], # POST, GET her şeye izin ver
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

# main.py içindeki analyze fonksiyonunu bu zeki versiyonla değiştir:
@app.post("/analyze")
async def analyze(incident: Incident):
    DEPLOYMENT_TOKEN = "f3baa2a32be542f9af98a81aa71da611"
    DEPLOYMENT_ID = "685958564177fe899cd68b64e5f7fe1b" 
    
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    payload = {
        "deploymentToken": DEPLOYMENT_TOKEN,
        "deploymentId": DEPLOYMENT_ID,
        "messages": [{"role": "user", "content": incident.text}]
    }

    try:
        response = requests.post(url, json=payload, timeout=30)
        ai_data = response.json()
        
        # AI'dan gelen ham metni alıyoruz
        raw_content = ai_data.get("result", {}).get("content", "")
        
        # BURASI KRİTİK: AI'dan gelen cevabı JSON olarak okumaya çalışıyoruz
        import json
        try:
            # Metnin başındaki ve sonundaki ```json gibi işaretleri temizleyip objeye çeviriyoruz
            clean_content = raw_content.replace('```json', '').replace('```', '').strip()
            parsed_ai = json.loads(clean_content)
            
            return {
                "boot_log": parsed_ai.get("boot_log", "[OK] AI Core Active"),
                "final_decision": parsed_ai.get("final_decision", "ANALİZ TAMAMLANDI"),
                "analysis": parsed_ai.get("analysis", ""),
                "action_plan": parsed_ai.get("action_plan", ["Aksiyon planı oluşturulamadı."]),
                "veto": parsed_ai.get("veto", "VETO Kararı Bulunmuyor")
            }
        except:
            # Eğer AI JSON formatında değil de düz yazı olarak cevap verirse (Hata koruması)
            return {
                "boot_log": "[SENTEZ_HATASI] AI düz metin döndürdü.",
                "final_decision": "DETAYLI ANALİZ",
                "analysis": raw_content,
                "action_plan": ["Lütfen yukarıdaki analiz metnini inceleyin."],
                "veto": "AI tarafından metin içinde belirtildi."
            }
            
    except Exception as e:
        return {"boot_log": "❌ HATA", "final_decision": "BAĞLANTI YOK", "analysis": str(e), "action_plan": [], "veto": "Yok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)