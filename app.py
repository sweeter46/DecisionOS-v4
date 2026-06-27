from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
import os
import uvicorn
import json

app = FastAPI()

# CORS Ayarları: Web sitesinin sunucuya erişmesine izin verir
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
    
    # Abacus'un kabul ettiği en kararlı mesaj formatı
    messages_list = [{"is_user": True, "text": incident.text}]
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": messages_list
    }

    try:
        # İLK DENEME: Standart liste gönderimi
        response = requests.post(url, json=payload, timeout=35)
        ai_data = response.json()
        
        # OTOMATİK DÜZELTME: Eğer liste hatası verirse formatı değiştirip tekrar dene
        if ai_data.get("error") and "must be a list" in str(ai_data.get("error")):
            payload["messages"] = json.dumps(messages_list) 
            response = requests.post(url, json=payload, timeout=35)
            ai_data = response.json()

        # VERİ YAKALAMA SİSTEMİ
        if ai_data.get("success") == True:
            res = ai_data.get("result", {})
            
            # Abacus'un cevabı koyabileceği tüm olası anahtarları tek tek kontrol ediyoruz
            final_report = (
                res.get("content") or 
                res.get("text") or 
                res.get("response") or 
                res.get("answer") or
                (res if isinstance(res, str) else None)
            )

            # Eğer yukarıdakilerin hiçbiri dolu değilse, ham veriyi analiz etmemiz için gönder
            if not final_report:
                final_report = f"Bağlantı kuruldu ancak rapor formatı farklı. Ham Veri: {str(ai_data)}"
            
            return {"report": final_report}
        else:
            # Abacus direkt hata döndürürse
            error_detail = ai_data.get("error") or "Bilinmeyen Abacus Hatası"
            return {"report": f"Abacus Sistem Yanıtı: {error_detail}"}
            
    except Exception as e:
        return {"report": f"Sunucu tarafında bir hata oluştu: {str(e)}"}

if __name__ == "__main__":
    # Render'ın portunu otomatik ayarla
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)