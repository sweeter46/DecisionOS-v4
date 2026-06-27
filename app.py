from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json

app = FastAPI()

# CORS Ayarları: Web sitesinin sunucuyla güvenli iletişim kurmasını sağlar.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    # Abacus AI'nın beklediği en güncel mesaj listesi formatı
    messages_list = [{"is_user": True, "text": incident.text}]
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": messages_list
    }

    try:
        # İSTEK GÖNDERİMİ
        response = requests.post(url, json=payload, timeout=40)
        ai_data = response.json()
        
        # OTOMATİK FORMAT DÜZELTME (Eğer Abacus liste hatası verirse)
        if ai_data.get("error") and "must be a list" in str(ai_data.get("error")):
            payload["messages"] = json.dumps(messages_list) 
            response = requests.post(url, json=payload, timeout=40)
            ai_data = response.json()

        # VERİ AYIKLAMA MOTORU (SCREENSHOT_50 ANALİZİNE GÖRE)
        if ai_data.get("success") == True:
            res = ai_data.get("result", {})
            messages = res.get("messages", [])
            
            final_report = ""
            
            # Mesajlar listesini tara ve AI'nın cevabını (is_user: False olan) bul
            for msg in messages:
                if msg.get("is_user") == False:
                    # AI'nın metnini al
                    final_report = msg.get("text") or msg.get("content")
                    break
            
            # Eğer listede bulamazsak klasik anahtarları dene
            if not final_report:
                final_report = res.get("content") or res.get("text") or res.get("response") or str(res)

            # TEMİZLİK: Markdown kutucuklarını ve JSON kalıntılarını sil (Daha şık bir görünüm için)
            final_report = final_report.replace("```json", "").replace("```", "").strip()
            
            return {"report": final_report}
        
        else:
            # Hata durumunda Abacus'tan gelen mesajı göster
            return {"report": f"Abacus Sistem Yanıtı: {ai_data.get('error')}"}
            
    except Exception as e:
        # Sunucu tarafında oluşabilecek genel hatalar
        return {"report": f"Strateji Sentezlenirken Hata Oluştu: {str(e)}"}

if __name__ == "__main__":
    # Render'ın port yönetim sistemi
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)