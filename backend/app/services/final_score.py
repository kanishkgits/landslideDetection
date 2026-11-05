"""Composite landslide screening index.

This is a transparent, heuristic research index (0-100), NOT a calibrated
probability. Components combine reported-event history, proximity/recency,
the existing relative ML score, and recent rainfall/soil-moisture conditions.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, float(value)))


def _rainfall_score(features: dict[str, Any]) -> float | None:
    """Heuristic wetness trigger score using cumulative rainfall in mm."""
    values = [features.get(k) for k in ("rain_24h_mm", "rain_72h_mm", "rain_7d_mm")]
    if any(v is None for v in values):
        return None
    r24, r72, r7 = [max(0.0, float(v)) for v in values]
    # Saturating scales: 30 mm/24h, 60 mm/72h, 150 mm/7d.
    return _clamp(
        100.0 * (
            0.40 * min(r24 / 30.0, 1.0)
            + 0.35 * min(r72 / 60.0, 1.0)
            + 0.25 * min(r7 / 150.0, 1.0)
        )
    )


def _soil_moisture_score(features: dict[str, Any]) -> float | None:
    vals = [
        features.get("soil_moisture_0_7cm_pct"),
        features.get("soil_moisture_7_28cm_pct"),
    ]
    vals = [float(v) for v in vals if v is not None]
    if not vals:
        return None
    # Soil moisture is expressed as percent volumetric water content.
    # This is a simple normalized indicator, not a soil-specific threshold.
    return _clamp(sum(vals) / len(vals))


def calculate_final_screening_score(
    history: dict[str, Any],
    ml_relative_score: float | None,
    features: dict[str, Any],
) -> dict[str, Any]:
    """Return a weighted 0-100 screening index and its component breakdown.

    Weights: historical count 30%, nearest-event proximity 20%, event recency
    10%, ML relative score 20%, rainfall 15%, soil moisture 5%.
    Missing components are excluded and remaining weights are renormalized.
    """
    components: dict[str, dict[str, Any]] = {}

    count = int(history.get("events_within_radius", 0) or 0)
    count10 = int(history.get("events_within_10km", 0) or 0)
    nearest = history.get("nearest_reported_event_km")
    newest_age_days = history.get("nearest_event_age_days")

    # Count score increases smoothly with reported event count.
    count_score = 100.0 * (1.0 - math.exp(-count / 12.0))
    # Nearby records carry more spatial evidence than records near radius edge.
    proximity_score = (
        100.0 * math.exp(-max(0.0, float(nearest)) / 20.0)
        if nearest is not None else None
    )
    # Recent reports contribute more. Unknown dates are omitted, not assumed recent.
    recency_score = (
        100.0 * math.exp(-max(0.0, float(newest_age_days)) / (365.0 * 8.0))
        if newest_age_days is not None else None
    )

    components["historical_event_count"] = {
        "score": round(count_score, 2), "weight": 0.30,
        "observed_value": count, "description": "Reported events within 25 km",
    }
    components["nearest_event_proximity"] = {
        "score": round(proximity_score, 2) if proximity_score is not None else None,
        "weight": 0.20, "observed_value_km": nearest,
        "description": "Closer reported events contribute more",
    }
    components["event_recency"] = {
        "score": round(recency_score, 2) if recency_score is not None else None,
        "weight": 0.10, "observed_value_age_days": newest_age_days,
        "description": "More recent reported events contribute more",
    }

    if ml_relative_score is not None:
        components["ml_relative_event_score"] = {
            "score": round(_clamp(float(ml_relative_score) * 100.0), 2),
            "weight": 0.20,
            "description": "Existing model discrimination score; not calibrated probability",
        }

    rain_score = _rainfall_score(features)
    if rain_score is not None:
        components["recent_rainfall"] = {
            "score": round(rain_score, 2), "weight": 0.15,
            "description": "Heuristic accumulation score from 24h, 72h and 7d rainfall",
        }

    moisture_score = _soil_moisture_score(features)
    if moisture_score is not None:
        components["soil_moisture"] = {
            "score": round(moisture_score, 2), "weight": 0.05,
            "description": "Normalized soil-moisture indicator; not soil-specific",
        }

    available = [
        (item["score"], item["weight"])
        for item in components.values()
        if item["score"] is not None
    ]
    total_weight = sum(weight for _, weight in available)
    final_score = (
        sum(score * weight for score, weight in available) / total_weight
        if total_weight else 0.0
    )

    inventory_available = bool(history.get("historical_event_count", 0))
    return {
        "final_landslide_screening_score": round(final_score, 1),
        "score_scale": "0-100 research screening index",
        "score_label": "COMPOSITE LANDSLIDE SCREENING INDEX",
        "interpretation": (
            "Heuristic screening index combining inventory evidence and "
            "environmental indicators. It is NOT a probability, calibrated "
            "forecast, official warning, or evacuation instruction."
        ),
        "component_weights_used": {
            key: item["weight"] for key, item in components.items()
            if item["score"] is not None
        },
        "components": components,
        "available_weight_fraction": round(total_weight, 3),
        "inventory_available": inventory_available,
        "limitations": [
            "Historical inventory is incomplete and affected by reporting bias.",
            "Pseudo-absence-trained ML output is a relative score, not probability.",
            "Rainfall and soil-moisture scales are heuristic and not locally calibrated.",
            "Slope, geology, land cover, drainage and soil properties are not yet included.",
        ],
    }
