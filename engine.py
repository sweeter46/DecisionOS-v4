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
    # Dinamik Senaryo: Eğitim ve Grafik Odaklı Test Verisi
    return {
        "title": "EĞİTİM ANALİZİ: MATEMATİK & İSTATİSTİK",
        "description": "Öğrencinin 5 günlük çalışma performansı analiz edildi. Veriler artış eğilimindedir.",
        "table_data": [
            {"Gun": "Pazartesi", "Saat": 2},
            {"Gun": "Salı", "Saat": 3},
            {"Gun": "Çarşamba", "Saat": 1},
            {"Gun": "Perşembe", "Saat": 4},
            {"Gun": "Cuma", "Saat": 5}
        ],
        "chart_labels": ["Pzt", "Sal", "Çar", "Per", "Cum"],
        "chart_values": [2, 3, 1, 4, 5],
        "math_formula": "\\bar{x} = \\frac{\\sum_{i=1}^{n} x_i}{n} = 3.0",
        "analysis": "Ortalama çalışma süresi günlük 3 saattir. Çarşamba günü verimlilik düşüşü saptanmıştır."
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)