from datetime import datetime, timezone
import httpx

FORECAST_URL="https://api.open-meteo.com/v1/forecast"

async def get_live_features(latitude:float,longitude:float):
    params={
      "latitude":latitude,"longitude":longitude,
      "hourly":"precipitation,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm",
      "past_days":7,"forecast_days":1,"timezone":"UTC"
    }
    async with httpx.AsyncClient(timeout=45) as client:
        r=await client.get(FORECAST_URL,params=params); r.raise_for_status(); data=r.json()
    h=data.get("hourly",{})
    rain=h.get("precipitation",[])
    sm0=h.get("soil_moisture_0_to_7cm",[])
    sm1=h.get("soil_moisture_7_to_28cm",[])
    def total(n):
        vals=[float(v) for v in rain[-n:] if v is not None]
        return sum(vals) if vals else None
    def mean_pct(values):
        vals=[float(v) for v in values[-24:] if v is not None]
        return sum(vals)/len(vals)*100 if vals else None
    return {
      "rain_24h_mm":total(24),"rain_72h_mm":total(72),"rain_7d_mm":total(168),
      "soil_moisture_0_7cm_pct":mean_pct(sm0),
      "soil_moisture_7_28cm_pct":mean_pct(sm1),
      "elevation_m":data.get("elevation"),
      "weather_source":"Open-Meteo Forecast API",
      "source_model":"Best Match; hourly precipitation and soil moisture",
      "retrieved_at":datetime.now(timezone.utc).isoformat(),
      "timezone":"UTC"
    }
