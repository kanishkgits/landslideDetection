import json, random
from datetime import datetime, timezone
from pathlib import Path
random.seed(7)
# Fictional demo stations across India; values are fabricated for interface testing.
stations = [
 ("DEMO-HIM-01","Uttarakhand",30.3,79.0,32,120,260,410,34,2200,78),
 ("DEMO-HIM-02","Himachal Pradesh",31.1,77.2,8,42,80,130,28,1800,48),
 ("DEMO-NE-01","Sikkim",27.5,88.5,24,95,180,290,39,2100,72),
 ("DEMO-WG-01","Kerala",10.3,76.9,12,65,140,260,22,600,66),
 ("DEMO-NE-02","Arunachal Pradesh",28.2, k:=94.7, 18,72,155,240,31,1900,69),
 ("DEMO-EAST-01","Jharkhand",23.6,85.3,2,10,18,35,6,500,22),
 ("DEMO-WEST-01","Maharashtra",19.7,73.5,5,28,60,105,17,900,42),
 ("DEMO-SOUTH-01","Karnataka",12.9,75.2,3,16,38,72,19,750,35)
]
rows=[]
for sid,state,lat,lon,r1,r24,r72,r7,slope,elev,moist in stations:
    rows.append({"location_id":sid,"state":state,"latitude":lat,"longitude":lon,
      "rain_1h_mm":r1,"rain_24h_mm":r24,"rain_72h_mm":r72,"rain_7d_mm":r7,
      "slope_deg":slope,"elevation_m":elev,"soil_moisture_pct":moist,
      "source":"SYNTHETIC_SIMULATOR","observed_at":datetime.now(timezone.utc).isoformat()})
out=Path(__file__).resolve().parents[2]/"data"/"demo_observations.json"
out.parent.mkdir(parents=True,exist_ok=True)
out.write_text(json.dumps(rows,indent=2))
print(f"Wrote {len(rows)} SYNTHETIC demo stations to {out}")
