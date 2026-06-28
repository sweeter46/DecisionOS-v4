import logging, requests, json, os, uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_headers=["*"], allow_methods=["*"])

class Incident(BaseModel):
    text: str

@app.post("/analyze")
async def analyze(incident: Incident):
    url = "https://api.abacus.ai/api/v0/getChatResponse"
    
    payload = {
        "deploymentToken": "f3baa2a32be542f9af98a81aa71da611",
        "deploymentId": "63a2ddb70",
        "messages": json.dumps([{"is_user": True, "text": incident.text}])
    }

    try:
        response = requests.post(url, json=payload, timeout=90)
        ai_data = response.json()
        
        # Abacus'tan gelen mesajı al
        raw_response = next((m for m in reversed(ai_data["result"]["messages"]) if not m.get("is_user")), {})
        text_content = raw_response.get("text", "")

        # --- KRİTİK GÜNCELLEME: FILES İÇERİĞİNİ YAKALA ---
        try:
            # Eğer text_content bir JSON string ise onu objeye çevir
            inner_json = json.loads(text_content)
            
            # Ana analiz metnini al
            final_text = inner_json.get("analysis", "")
            
            # EĞER FILES VARSA, ONLARI DA ANALİZE EKLE (GRAFİK BURADA OLABİLİR!)
            if "files" in inner_json and len(inner_json["files"]) > 0:
                for file in inner_json["files"]:
                    final_text += f"\n\n### EK DOSYA İÇERİĞİ ({file.get('path')}):\n{file.get('content')}"
            
            # Dashboard'a birleştirilmiş metni yolla
            return {
                "report": {
                    "final_decision": inner_json.get("final_decision", "ANALİZ"),
                    "analysis": final_text,
                    "action_plan": inner_json.get("action_plan", {"0-1h": []}),
                    "confidence": inner_json.get("confidence", 0.95)
                },
                "status": "success"
            }
        except:
            # Eğer JSON parse edilemezse ham metni yolla
            return {"report": {"analysis": text_content}, "status": "partial"}

    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))