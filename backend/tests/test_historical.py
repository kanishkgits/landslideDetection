import pandas as pd
from app.services.historical import historical_evidence

def test_more_nearby_reported_events_increase_index():
    one = pd.DataFrame([{"event_date":"2015-01-01","latitude":27.0,"longitude":88.0}])
    many = pd.DataFrame([
        {"event_date":"2015-01-01","latitude":27.0,"longitude":88.0},
        {"event_date":"2016-01-01","latitude":27.01,"longitude":88.01},
        {"event_date":"2017-01-01","latitude":27.02,"longitude":88.02},
    ])
    a = historical_evidence(27.0,88.0,one)
    b = historical_evidence(27.0,88.0,many)
    assert b["historical_occurrence_index"] > a["historical_occurrence_index"]
    assert b["events_within_radius"] > a["events_within_radius"]

def test_no_inventory_is_zero_not_safe_label():
    result = historical_evidence(25.6,85.1,pd.DataFrame())
    assert result["historical_occurrence_index"] == 0
    assert "NO INVENTORY" in result["historical_index_label"]
