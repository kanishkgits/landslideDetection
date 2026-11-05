import json
from pathlib import Path
DATA = Path(__file__).resolve().parents[3] / "data"
def load_observations():
    p = DATA / "demo_observations.json"
    if not p.exists():
        return []
    return json.loads(p.read_text())
def load_alerts():
    from app.services.risk import assess_risk
    alerts = []
    for item in load_observations():
        r = assess_risk(item)
        if r["risk_level"] in ("HIGH", "CRITICAL"):
            alerts.append({**r, "alert_type": "DEMO_THRESHOLD_CROSSING"})
    return alerts
