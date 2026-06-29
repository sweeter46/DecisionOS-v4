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
    # Geometri Sınav Sorusu ve Çözüm Verisi
    return {
        "title": "GEOMETRİ SINAVI: ANALİTİK DÜZLEM VE DÖNEL CİSİMLER",
        "description": "SORU: Köşeleri A(0,0), B(6,0) ve C(3,4) olan bir ABC üçgeni, x-ekseni etrafında 360 derece döndürülüyor. Oluşan cismin kesit alanındaki değişimi grafik üzerinde inceleyiniz ve toplam hacmi bulunuz.",
        "table_data": [
            {"Bileşen": "Taban Uzunluğu", "Değer": "6 Birim"},
            {"Bileşen": "Tepe Yüksekliği (r)", "Değer": "4 Birim"},
            {"Bileşen": "A Noktası", "Değer": "(0,0)"},
            {"Bileşen": "B Noktası", "Değer": "(6,0)"},
            {"Bileşen": "C Noktası", "Değer": "(3,4)"}
        ],
        "chart_labels": ["0°", "90°", "180°", "270°", "360°"],
        "chart_values": [0, 16, 32, 16, 0], # Kesit alanının dönüş esnasındaki varyasyonu
        "math_formula": "V_{total} = \\frac{1}{3}\\pi r^2 h = \\frac{1}{3}\\pi (4^2) \\cdot 6 = 32\\pi \\text{ br}^3",
        "analysis": "Çözüm: Üçgen döndürüldüğünde r=4 olan iki birleşik koni oluşur. Hacim formülü ile sonuç 32π birimküp olarak hesaplanır."
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)