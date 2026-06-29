import os
import uvicorn
import requests
import json
import re
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Logları takip etmek için (Render loglarında hatayı görmek istersen)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --- KRİTİK AYARLAR ---
API_KEY = "sk_..." # Buraya kendi anahtarını yapıştır (Tırnak içinde kalsın)
DEPLOYMENT_ID = "..." # Buraya kendi id'ni yapıştır (Tırnak içinde kalsın)
# ----------------------

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # Abacus'a hem konuyu anlatmasını hem de bizim tablo/grafik formatımızda JSON üretmesini söylüyoruz
    prompt = f"""
    Sen profesyonel bir eğitmensin. Konu: {incident.text}
    Lütfen bu konuyu açıkla ve mutlaka aşağıdaki JSON formatında cevap dön.
    JSON yapısı:
    {{
        "title": "Ünite Başlığı",
        "description": "Konunun kısa ve net anlatımı",
        "type": "bar",
        "table_data": [{{"Bilgi": "X", "Detay": "Y"}}, {{"Bilgi": "Z", "Detay": "T"}}],
        "chart_labels": ["Label1", "Label2", "Label3"],
        "chart_values": [10, 20, 30],
        "math_formula": "LaTeX_Buraya",
        "analysis": "Öğrenci için kritik ipucu ve özet."
    }}
    JSON dışında tek bir harf bile yazma. Formatı sakın bozma.
    """

    url = f"https://abacus.ai/api/v0/getChatResponse?deploymentToken={API_KEY}&deploymentId={DEPLOYMENT_ID}"
    
    try:
        # Timeout'u 60 saniyeye çıkarıyoruz ki "Connection Reset" vermesin
        response = requests.post(url, json={"messages": [{"is_user": True, "text": prompt}]}, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Abacus Error: {response.text}")
            return {"title": "Sistem Meşgul", "description": "AI şu an cevap veremiyor.", "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Hata kodu: " + str(response.status_code)}

        res_json = response.json()
        raw_text = res_json['result']['text']
        
        # Karmaşık cevabın içinden sadece JSON kısmını cımbızla çekiyoruz
        json_match = re.search(r'(\{.*\})', raw_text, re.DOTALL)
        
        if json_match:
            return json.loads(json_match.group(1))
        else:
            return {
                "title": "Format Hatası",
                "description": "AI serbest metin üretti, JSON bulunamadı.",
                "table_data": [{"Cevap": "AI Yanıtı"}, {"Metin": raw_text[:50] + "..."}],
                "chart_labels": ["Hata"], "chart_values": [0], "math_formula": "", "analysis": "Lütfen tekrar deneyin."
            }

    except requests.exceptions.Timeout:
        return {"title": "Zaman Aşımı", "description": "AI düşünürken bağlantı koptu. Lütfen tekrar deneyin.", "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Süre doldu."}
    except Exception as e:
        logger.error(f"Genel Hata: {str(e)}")
        return {"title": "Bağlantı Hatası", "description": str(e), "table_data": [], "chart_labels": [], "chart_values": [], "math_formula": "", "analysis": "Teknik bir sorun oluştu."}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)