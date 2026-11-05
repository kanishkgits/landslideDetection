from app.services.final_score import calculate_final_screening_score

def test_more_historical_events_increase_final_score():
    features = {
        "rain_24h_mm": 0, "rain_72h_mm": 0, "rain_7d_mm": 0,
        "soil_moisture_0_7cm_pct": 20,
        "soil_moisture_7_28cm_pct": 20,
    }
    base = {
        "historical_event_count": 100,
        "events_within_10km": 0,
        "nearest_reported_event_km": 24,
        "nearest_event_age_days": 2000,
    }
    few = dict(base, events_within_radius=1)
    many = dict(base, events_within_radius=20)
    a = calculate_final_screening_score(few, 0.3, features)
    b = calculate_final_screening_score(many, 0.3, features)
    assert b["final_landslide_screening_score"] > a["final_landslide_screening_score"]

def test_missing_components_are_renormalized():
    history = {
        "historical_event_count": 0, "events_within_radius": 0,
        "events_within_10km": 0, "nearest_reported_event_km": None,
        "nearest_event_age_days": None,
    }
    result = calculate_final_screening_score(history, None, {})
    assert result["available_weight_fraction"] == 0.3
    assert result["final_landslide_screening_score"] == 0.0
