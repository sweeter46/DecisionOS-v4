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
        messages = ai_data.get("result", {}).get("messages", [])
        raw_msg = next((m for m in reversed(messages) if not m.get("is_user")), {}).get("text", "")

        try:
            # JSON paketini aç
            inner = json.loads(raw_msg)
            full_analysis = inner.get("analysis", "")
            
            # --- KRİTİK NOKTA: GİZLİ DOSYALARI (GRAPH/TABLE) METNE EKLE ---
            # AI eğer grafik kodunu "files" içine koyduysa onu metne geri alıyoruz
            if "files" in inner and isinstance(inner["files"], list):
                for f in inner["files"]:
                    if f.get("content"):
                        full_analysis += f"\n\n{f.get('content')}"
            
            return {
                "report": {
                    "final_decision": inner.get("final_decision", "ANALİZ"),
                    "analysis": full_analysis, # ARTIK GRAFİK BURADA!
                    "confidence": inner.get("confidence", 0.95)
                },
                "status": "success"
            }
        except:
            return {"report": {"analysis": raw_msg}, "status": "partial"}
    except Exception as e:
        return {"report": str(e), "status": "error"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))