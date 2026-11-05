"""Historical reported-landslide evidence from the available event inventory.

All outputs describe the loaded inventory, not complete hazard truth.
"""
from __future__ import annotations

from pathlib import Path
import math
import pandas as pd

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(min(1.0, math.sqrt(a)))


def load_inventory(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=["event_date", "latitude", "longitude", "_date"])
    df = pd.read_csv(path, low_memory=False)
    normalized = {str(c).strip().lower().replace(" ", "_"): c for c in df.columns}
    aliases = {
        "latitude": ("latitude", "lat"),
        "longitude": ("longitude", "lon", "lng"),
        "event_date": ("event_date", "date", "eventdate"),
        "country": ("country", "country_name", "countryname"),
    }
    rename = {}
    for target, candidates in aliases.items():
        for candidate in candidates:
            if candidate in normalized:
                rename[normalized[candidate]] = target
                break
    df = df.rename(columns=rename)
    required = {"latitude", "longitude"}
    if not required.issubset(df.columns):
        raise ValueError(
            f"Inventory missing latitude/longitude columns. Found: {list(df.columns)}. "
            "Run app.ml.real_data.download_catalog to create the normalized India CSV."
        )
    if "country" in df.columns:
        df = df[df["country"].astype(str).str.strip().str.casefold().isin(["india", "in"])]
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"]).copy()
    df = df[df.latitude.between(6, 37.5) & df.longitude.between(68, 98)]
    if "event_date" not in df:
        df["event_date"] = None
    df["_date"] = pd.to_datetime(df["event_date"], errors="coerce", utc=True)
    return df


def historical_evidence(latitude: float, longitude: float, inventory: pd.DataFrame,
                        radius_km: float = 25.0) -> dict:
    if "_date" not in inventory.columns:
        inventory = inventory.copy()
        inventory["_date"] = pd.to_datetime(
            inventory["event_date"], errors="coerce", utc=True
        ) if "event_date" in inventory.columns else pd.NaT

    if inventory.empty:
        return {
            "historical_event_count": 0,
            "events_within_10km": 0,
            "events_within_radius": 0,
            "nearest_reported_event_km": None,
            "nearest_event_age_days": None,
            "historical_occurrence_index": 0.0,
            "historical_index_label": "NO INVENTORY RECORDS AVAILABLE",
            "radius_km": radius_km,
            "nearby_events": [],
        }

    distances = inventory.apply(
        lambda r: haversine_km(
            latitude, longitude, float(r.latitude), float(r.longitude)
        ),
        axis=1,
    )
    nearby_mask = distances <= radius_km
    nearby = inventory.loc[nearby_mask].copy()
    nearby_dist = distances.loc[nearby_mask]

    weighted = float(
        (2.0 ** (-distances[nearby_mask] / 10.0)).sum()
    )
    index = 100.0 * (1.0 - math.exp(-weighted / 3.0))

    valid_dates = nearby["_date"].dropna()
    now = pd.Timestamp.now(tz="UTC")
    newest_age_days = (
        max(0.0, (now - valid_dates.max()).total_seconds() / 86400.0)
        if not valid_dates.empty else None
    )

    nearby_events = []
    for i, r in nearby.iterrows():
        event_date = r["_date"]
        nearby_events.append({
            "event_date": event_date.date().isoformat() if pd.notna(event_date) else None,
            "latitude": float(r.latitude),
            "longitude": float(r.longitude),
            "distance_km": round(float(nearby_dist.loc[i]), 2),
        })

    return {
        "historical_event_count": int(len(inventory)),
        "events_within_10km": int((distances <= 10).sum()),
        "events_within_radius": int(len(nearby)),
        "nearest_reported_event_km": round(float(distances.min()), 2),
        "nearest_event_age_days": round(newest_age_days, 1) if newest_age_days is not None else None,
        "historical_occurrence_index": round(index, 1),
        "historical_index_label": "HISTORICAL REPORTED-EVENT EVIDENCE (NOT PROBABILITY)",
        "radius_km": radius_km,
        "nearby_events": nearby_events[:50],
    }
