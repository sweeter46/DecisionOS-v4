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
    userInput = incident.text.lower()

    # 1. GEOMETRİ SENARYOSU
    if "geometri" in userInput or "üçgen" in userInput:
        return {
            "title": "NEURAL GEOMETRY ANALİZİ",
            "description": "ABC üçgeninde iç açılar ve kenar bağıntıları hesaplandı.",
            "type": "radar",
            "table_data": [{"Açı": "A", "Deg": 40}, {"Açı": "B", "Deg": 60}, {"Açı": "C", "Deg": 80}],
            "chart_labels": ["A Açısı", "B Açısı", "C Açısı"],
            "chart_values": [40, 60, 80],
            "math_formula": "A+B+C = 180^\\circ",
            "analysis": "İç açılar toplamı 180 derecedir. Üçgen dar açılıdır."
        }

    # 2. SINAV / EĞİTİM SENARYOSU
    elif "sınav" in userInput or "not" in userInput or "başarı" in userInput:
        return {
            "title": "EĞİTİM VE BAŞARI ANALİZİ",
            "description": "Dönem içi ders performans verileri bar grafik olarak işlendi.",
            "type": "bar",
            "table_data": [{"Ders": "Matematik", "Not": 85}, {"Ders": "Fizik", "Not": 70}, {"Ders": "Türkçe", "Not": 95}],
            "chart_labels": ["Matematik", "Fizik", "Türkçe"],
            "chart_values": [85, 70, 95],
            "math_formula": "\\bar{x} = 83.3",
            "analysis": "Sözel ders başarısı sayısalın üzerindedir. Fizik dersine odaklanılmalı."
        }

    # 3. VARSAYILAN / KRİZ SENARYOSU
    else:
        return {
            "title": "STRATEJİK KRİZ YÖNETİMİ",
            "description": f"Girişi yapılan '{incident.text}' konusu kriz protokolünde analiz edildi.",
            "type": "line",
            "table_data": [{"Risk": "Kritik", "Seviye": "L8"}, {"Güven": "Yüksek", "Oran": "%92"}],
            "chart_labels": ["Başlangıç", "Süreç", "Final"],
            "chart_values": [10, 45, 95],
            "math_formula": "\\Delta Risk = f(t)",
            "analysis": "Süreç stabil seyretmektedir. Operasyonel risk seviyesi L8."
        }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)