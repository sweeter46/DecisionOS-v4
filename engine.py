import os
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
    userInput = incident.text.lower() # Küçük harfe çevirip ne istediğini anlayalım

    # 1. SENARYO: GEOMETRİ/ÜÇGEN İSTERSE
    if "geometri" in userInput or "üçgen" in userInput:
        return {
            "title": "NEURAL GEOMETRY ANALİZİ",
            "description": "ABC üçgeninde kenar ve iç açı ilişkileri Core-Prometheus tarafından işlendi.",
            "table_data": [
                {"Bileşen": "A Açısı", "Değer": "40°"},
                {"Bileşen": "B Açısı", "Değer": "60°"},
                {"Bileşen": "C Açısı", "Değer": "80°"}
            ],
            "chart_labels": ["A", "B", "C"],
            "chart_values": [40, 60, 80],
            "math_formula": "A+B+C = 180^\\circ",
            "analysis": "İç açılar toplamı korunmuştur. Üçgen dar açılıdır.",
            "type": "radar" # Radar grafik tipi
        }

    # 2. SENARYO: SINAV/BAŞARI İSTERSE
    elif "sınav" in userInput or "not" in userInput:
        return {
            "title": "ÖĞRENCİ PERFORMANS ANALİZİ",
            "description": "Dönem içi not ortalamaları ve gelişim eğrisi hesaplandı.",
            "table_data": [
                {"Ders": "Matematik", "Not": 85},
                {"Ders": "Fizik", "Not": 90},
                {"Ders": "Geometri", "Not": 75}
            ],
            "chart_labels": ["Mat", "Fiz", "Geo"],
            "chart_values": [85, 90, 75],
            "math_formula": "\\text{Ortalama} = \\frac{85+90+75}{3} = 83.3",
            "analysis": "Sayısal derslerde yüksek başarı saptanmıştır. Geometri için ek etüt önerilir.",
            "type": "bar" # Bar grafik tipi
        }

    # 3. SENARYO: HİÇBİRİ DEĞİLSE (GENEL KARAR SİSTEMİ)
    else:
        return {
            "title": "GENEL STRATEJİK ANALİZ",
            "description": f"Girişi yapılan '{incident.text}' konusu için nöral ağlar çalıştırıldı.",
            "table_data": [
                {"Risk": "Düşük", "Olasılık": "%20"},
                {"Risk": "Kritik", "Olasılık": "%5"}
            ],
            "chart_labels": ["Risk", "Güven", "Hız"],
            "chart_values": [20, 85, 95],
            "math_formula": "R(t) = \\int_{0}^{t} f(x)dx",
            "analysis": "Genel parametreler stabil. Eylem planı onaylandı.",
            "type": "line" # Çizgi grafik tipi
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)