"""Build a research case-control table from NASA India events + ERA5 reanalysis.

Positive = reported catalog event. Negative = spatially displaced pseudo-absence
matched to the event date. Negative is NOT a verified non-landslide.
"""
import argparse, asyncio, hashlib, json, math, random
from pathlib import Path
import pandas as pd
import httpx

ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"
FEATURES = ["rain_24h_mm","rain_72h_mm","rain_7d_mm",
            "soil_moisture_0_7cm_pct","soil_moisture_7_28cm_pct","elevation_m"]

def control_point(lat, lon, seed):
    rng = random.Random(seed)
    # 12-25 km offset; local matched control. Clamp to broad Indian bounds.
    distance = rng.uniform(12,25)
    bearing = rng.uniform(0,360)
    dlat = distance * math.cos(math.radians(bearing)) / 111.0
    dlon = distance * math.sin(math.radians(bearing)) / max(30, 111*math.cos(math.radians(lat)))
    return max(6.2,min(37.2,lat+dlat)), max(68.2,min(97.8,lon+dlon))

def cache_key(lat, lon, start, end):
    return hashlib.sha1(f"{lat:.3f}|{lon:.3f}|{start}|{end}".encode()).hexdigest()

async def fetch_weather(client, lat, lon, start, end, cache_dir):
    key = cache_key(lat,lon,start,end)
    path = cache_dir / f"{key}.json"
    if path.exists():
        return json.loads(path.read_text())
    params = {
        "latitude": lat, "longitude": lon, "start_date": start, "end_date": end,
        "hourly": "precipitation,soil_moisture_0_to_7cm,soil_moisture_7_to_28cm",
        "daily": "precipitation_sum", "timezone": "UTC", "models": "era5"
    }
    for attempt in range(3):
        try:
            response = await client.get(ARCHIVE, params=params)
            response.raise_for_status()
            data = response.json()
            path.write_text(json.dumps(data))
            return data
        except Exception:
            if attempt == 2: raise
            await asyncio.sleep(2*(attempt+1))

def summarize_weather(data):
    hourly = data.get("hourly", {})
    rain = pd.to_numeric(pd.Series(hourly.get("precipitation", [])), errors="coerce")
    sm0 = pd.to_numeric(pd.Series(hourly.get("soil_moisture_0_to_7cm", [])), errors="coerce")
    sm1 = pd.to_numeric(pd.Series(hourly.get("soil_moisture_7_to_28cm", [])), errors="coerce")
    if len(rain) < 168 or rain.tail(168).notna().sum() < 160:
        raise ValueError("Insufficient hourly precipitation values for a complete 7-day feature window")
    # Event date is excluded: only the seven full days before the reported date.
    return {
        "rain_24h_mm": float(rain.tail(24).sum()),
        "rain_72h_mm": float(rain.tail(72).sum()),
        "rain_7d_mm": float(rain.tail(168).sum()),
        "soil_moisture_0_7cm_pct": float(sm0.tail(24).mean()*100) if sm0.notna().any() else None,
        "soil_moisture_7_28cm_pct": float(sm1.tail(24).mean()*100) if sm1.notna().any() else None,
        "elevation_m": float(data.get("elevation")) if data.get("elevation") is not None else None
    }

async def main_async(args):
    events = pd.read_csv(args.events)
    required = {"event_date","latitude","longitude"}
    if not required.issubset(events.columns):
        raise ValueError(f"Events CSV must contain {sorted(required)}")
    events["event_date"] = pd.to_datetime(events.event_date, errors="coerce")
    events = events.dropna(subset=["event_date","latitude","longitude"])
    events = events[events.event_date >= "1950-01-08"].copy()
    events = events.sort_values("event_date")
    if args.max_events:
        events = events.tail(args.max_events)
    cache = Path(args.cache); cache.mkdir(parents=True, exist_ok=True)
    rows=[]
    timeout=httpx.Timeout(60, connect=20)
    limits=httpx.Limits(max_connections=4, max_keepalive_connections=2)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        for idx, ev in events.iterrows():
            event_date = ev.event_date.date()
            start=(event_date-pd.Timedelta(days=7)).isoformat()
            end=(event_date-pd.Timedelta(days=1)).isoformat()
            lat=float(ev.latitude); lon=float(ev.longitude)
            pair_id=str(ev.get("source_record_id", idx))
            points=[(lat,lon,1,"reported_event")]
            clat,clon=control_point(lat,lon,seed=int(hashlib.md5(pair_id.encode()).hexdigest()[:8],16))
            points.append((clat,clon,0,"matched_background_sample"))
            for plat,plon,label,sample_type in points:
                try:
                    await asyncio.sleep(0.15)
                    wx=await fetch_weather(client,plat,plon,start,end,cache)
                    feats=summarize_weather(wx)
                    if any(feats[k] is None or not math.isfinite(feats[k]) for k in ["rain_24h_mm","rain_72h_mm","rain_7d_mm","elevation_m"]):
                        raise ValueError("Missing rainfall/elevation features")
                    # Soil moisture can be missing in some reanalysis responses; the training pipeline imputes it.
                    rows.append({
                        "sample_id":f"{pair_id}-{label}", "pair_id":pair_id,
                        "event_date":event_date.isoformat(), "latitude":plat, "longitude":plon,
                        "landslide_reported":label, "sample_type":sample_type,
                        "weather_source":"Open-Meteo ERA5 reanalysis",
                        "catalog_source":"NASA Global Landslide Catalog", **feats
                    })
                except Exception as exc:
                    print(f"Skipped {pair_id} {sample_type}: {exc}")
    df=pd.DataFrame(rows)
    if df.empty: raise RuntimeError("No samples enriched. Check network/API and date range.")
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(out,index=False)
    print(f"Saved {len(df)} rows from {df.pair_id.nunique()} matched event pairs: {out.resolve()}")
    print(df.groupby(["sample_type"]).size().to_string())
    print("IMPORTANT: background samples are pseudo-absences, not verified non-landslide observations.")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--events",default="../data/processed/nasa_landslides_india.csv")
    p.add_argument("--out",default="../data/processed/india_event_case_control.csv")
    p.add_argument("--cache",default="../data/cache/open_meteo")
    p.add_argument("--max-events",type=int,default=250)
    args=p.parse_args()
    asyncio.run(main_async(args))
if __name__=="__main__": main()
