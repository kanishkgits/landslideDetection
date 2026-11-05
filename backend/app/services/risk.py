from datetime import datetime, timezone

def assess_risk(x: dict) -> dict:
    # Transparent screening heuristic for UI/API development only.
    # It is NOT a calibrated probability and must not be used for public warnings.
    rain = float(x.get("rain_24h_mm", 0))
    rain72 = float(x.get("rain_72h_mm", 0))
    rain7 = float(x.get("rain_7d_mm", 0))
    slope = float(x.get("slope_deg", 0))
    moisture = float(x.get("soil_moisture_pct", 0))
    # Monotonic, bounded screening score; deliberately called score, not probability.
    score = min(100.0, 0.30*min(rain, 250)/2.5 +
                0.20*min(rain72, 450)/4.5 +
                0.10*min(rain7, 700)/7.0 +
                0.20*min(slope, 45)/0.45 +
                0.20*moisture)
    if score >= 75: level = "CRITICAL"
    elif score >= 55: level = "HIGH"
    elif score >= 30: level = "MODERATE"
    else: level = "LOW"
    return {
        "location_id": x.get("location_id", "unknown"),
        "latitude": x.get("latitude"), "longitude": x.get("longitude"),
        "risk_score": round(score, 1), "risk_level": level,
        "score_type": "UNVALIDATED_HEURISTIC_NOT_PROBABILITY",
        "drivers": {"rain_24h_mm": rain, "rain_72h_mm": rain72,
                    "rain_7d_mm": rain7, "slope_deg": slope,
                    "soil_moisture_pct": moisture},
        "source": x.get("source", "unknown"),
        "observed_at": x.get("observed_at") or datetime.now(timezone.utc).isoformat()
    }
