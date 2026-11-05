from datetime import datetime, timezone
from pathlib import Path
import asyncio, os
import pandas as pd
import joblib
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from app.services.live_weather import get_live_features
from app.services.historical import load_inventory, historical_evidence
from app.services.final_score import calculate_final_screening_score

load_dotenv()
BASE=Path(__file__).resolve().parents[2]
MODEL_PATH=Path(os.getenv("MODEL_PATH",str(Path(__file__).resolve().parent/"ml"/"artifacts"/"terragaurd_event_model.joblib")))
if not MODEL_PATH.is_absolute(): MODEL_PATH=Path.cwd()/MODEL_PATH
DATA_DIR=Path(os.getenv("TERRAGUARD_DATA_DIR",str(BASE/"data")))
EVENTS_PATH=DATA_DIR/"processed"/"nasa_landslides_india.csv"

def get_inventory():
    return load_inventory(EVENTS_PATH)

app=FastAPI(title="TerraGuard API",version="1.0.0",
 description="India landslide research prototype using NASA catalog events and Open-Meteo weather data.")
origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,
                   allow_methods=["*"],allow_headers=["*"])

class AssessInput(BaseModel):
    latitude:float=Field(ge=6,le=37.5)
    longitude:float=Field(ge=68,le=98)

def load_model():
    if not MODEL_PATH.exists(): return None
    return joblib.load(MODEL_PATH)

@app.get("/health")
def health():
    catalog_count = 0
    catalog_error = None
    if EVENTS_PATH.exists():
        try:
            catalog_count = len(load_inventory(EVENTS_PATH))
        except Exception as exc:
            catalog_error = str(exc)
    return {
        "status": "ok",
        "service": "terragaurd-api",
        "model_ready": MODEL_PATH.exists(),
        "catalog_ready": EVENTS_PATH.exists() and catalog_count > 0,
        "catalog_path": str(EVENTS_PATH.resolve()),
        "catalog_event_count": catalog_count,
        "catalog_error": catalog_error,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/api/v1/events")
def events(limit:int=Query(100,ge=1,le=2000)):
    if not EVENTS_PATH.exists(): return {"items":[],"count":0,"source":"NASA_GLC","message":"Run data acquisition first."}
    df=pd.read_csv(EVENTS_PATH).head(limit)
    return {"items":df.astype(object).where(pd.notna(df),None).to_dict("records"),"count":len(df),
            "source":"NASA_GLC_STATIC_EXPORT",
            "inventory_note":"Reported events only; incomplete inventory; no-record locations are not verified negatives."}

@app.get("/api/v1/model/metrics")
def model_metrics():
    p=Path(__file__).resolve().parent/"ml"/"artifacts"/"metrics.json"
    if not p.exists(): raise HTTPException(404,"Train the model first.")
    import json
    return json.loads(p.read_text())

@app.get("/api/v1/historical/assess")
def historical_assess(latitude:float=Query(...,ge=6,le=37.5),
                      longitude:float=Query(...,ge=68,le=98),
                      radius_km:float=Query(25.0,ge=1,le=100)):
    """Return nearby inventory evidence; the index is not a landslide probability."""
    return historical_evidence(latitude, longitude, get_inventory(), radius_km)

@app.post("/api/v1/live/assess")
async def live_assess(payload:AssessInput):
    bundle=load_model()
    if bundle is None:
        raise HTTPException(503,"Model not trained. Run the real-data acquisition and training steps.")
    try:
        features=await get_live_features(payload.latitude,payload.longitude)
        cols=bundle["features"]
        row={k:features.get(k) for k in cols}
        if any(row.get(k) is None for k in ["rain_24h_mm","rain_72h_mm","rain_7d_mm","elevation_m"]):
            raise ValueError("Live weather feed returned missing rainfall/elevation features.")
        score=float(bundle["model"].predict_proba(pd.DataFrame([row]))[0,1])
        history = historical_evidence(
            payload.latitude, payload.longitude, get_inventory(), radius_km=25.0
        )
        final_score = calculate_final_screening_score(
            history=history,
            ml_relative_score=score,
            features=features,
        )
        return {
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "final_score": final_score,
            "historical_evidence": history,
            "relative_event_score": round(score, 4),
            "score_interpretation": bundle["score_interpretation"],
            "features": features,
            "data_mode": "LIVE_WEATHER_WITH_REANALYSIS_TRAINED_MODEL",
            "warning": (
                "Research prototype only. The composite score is a heuristic "
                "screening index, not calibrated probability or an official warning."
            ),
        }
    except HTTPException: raise
    except Exception as exc: raise HTTPException(502,f"Live assessment failed: {exc}")

@app.get("/api/v1/live/weather")
async def live_weather(latitude:float=Query(...,ge=6,le=37.5),
                       longitude:float=Query(...,ge=68,le=98)):
    try: return await get_live_features(latitude,longitude)
    except Exception as exc: raise HTTPException(502,f"Weather provider error: {exc}")

@app.websocket("/ws/monitoring")
async def monitoring_socket(ws:WebSocket):
    await ws.accept()
    try:
        while True:
            ready=MODEL_PATH.exists()
            await ws.send_json({"type":"system_status","model_ready":ready,
              "timestamp":datetime.now(timezone.utc).isoformat(),
              "message":"Live assessments are requested per location; no simulated sensor feed is used."})
            await asyncio.sleep(15)
    except WebSocketDisconnect: return
