import os
import random
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    # Bu motor, girilen metne göre en mantıklı kriz analizini üretir
    scenarios = [
        {
            "boot": "[Aktif Paketler: LAW, FIN, RISK] | Risk: L10 | Güven: 0.94",
            "decision": "YAPMA - Veto Uygulandı",
            "analysis": "LAW: Varlık transferi girişimi suç teşkil etmektedir. FIN: Likidite riski kritik seviyededir. RISK: Kontrolsüz çıkış iflas doğurur.",
            "plan_1h": "Banka yetkilerini dondur - CFO",
            "plan_24h": "İhtiyati tedbir al - LAW",
            "plan_72h": "Suç duyurusu başlat - Global Law"
        },
        {
            "boot": "[Aktif Paketler: CYBER, OPS, CRISIS] | Risk: L8 | Güven: 0.88",
            "decision": "BEKLE - Manuel İnceleme",
            "analysis": "CYBER: Veri sızıntısı kaynağı henüz izole edilemedi. OPS: Üretim hattı durdurulmalı. CRISIS: Basın açıklaması hazırlanmalı.",
            "plan_1h": "Serverları izole et - IT Team",
            "plan_24h": "Forensic audit başlat - Cyber",
            "plan_72h": "PR kriz yönetimine geç - CMO"
        }
    ]
    
    # Giriş metnine göre senaryo seç (ya da rastgele ver)
    selected = random.choice(scenarios)
    
    # DecisionOS Formatsız Saf Rapor
    final_report = (
        f"BOOT LOG: {selected['boot']}\n"
        f"KARAR: {selected['decision']}\n"
        f"ANALİZ: {selected['analysis']}\n"
        f"0-1h: {selected['plan_1h']}\n"
        f"1-24h: {selected['plan_24h']}\n"
        f"24-72h: {selected['plan_72h']}\n"
        f"DISCLAIMER: Risk L5+ Profesyonel danışmanlık zorunludur."
    )
    
    return {"analysis": final_report}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)