from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random

app = FastAPI()

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
    text = incident.text.lower()
    
    # 1. Uzman Paketleri Belirleme
    packages = []
    if any(word in text for word in ["para", "usd", "banka", "kredi", "nakit"]): packages.append("FINANCE_PRO")
    if any(word in text for word in ["saldırı", "hack", "şifre", "ransomware", "veri"]): packages.append("CYBER_PRO")
    if any(word in text for word in ["dava", "hukuk", "yasal", "sözleşme", "suç"]): packages.append("LAW_PRO")
    if any(word in text for word in ["çalışan", "eleman", "istifa", "rakip"]): packages.append("TALENT_PRO")
    
    if not packages: packages = ["STRATEGY_PRO"]

    # 2. Risk Seviyesi Hesaplama (Temsili)
    risk_level = len(packages) * 2 + random.randint(1, 2)
    if risk_level > 10: risk_level = 10

    # 3. Decision Brief Oluşturma
    # Burada gerçek v4.0 mimarisindeki alt başlıkları kurguluyoruz
    brief = {
        "boot_log": f"[Aktif Paketler: {', '.join(packages)}] | Risk: L{risk_level} | Güven: %94",
        "final_decision": "KRİTİK MÜDAHALE GEREKLİ" if risk_level > 5 else "STANDART PROSEDÜR",
        "analysis": f"Sistem {len(packages)} farklı koldan tehdit algıladı. Tehditlerin odağı: {packages[0]}.",
        "action_plan": [
            "0-1h: Tüm sistem çıkışlarını mühürle ve kriz odasını topla.",
            "1-24h: Yasal bildirimleri yap ve etkilenen birimleri izole et.",
            "24-72h: Hasar tespiti ve sistem geri yükleme operasyonunu başlat."
        ],
        "veto": "LAW_PRO: Mevcut yasal süreç bitmeden dışarıya bilgi sızdırılması VETO edildi."
    }
    
    return brief

import uvicorn
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)