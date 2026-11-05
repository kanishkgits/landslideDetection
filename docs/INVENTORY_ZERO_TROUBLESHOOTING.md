# Historical index is zero everywhere: diagnosis

The API reads exactly this file by default:
`TerraGuard/data/processed/nasa_landslides_india.csv`
(override with `TERRAGUARD_DATA_DIR`; the file must be under
`<TERRAGUARD_DATA_DIR>/processed/nasa_landslides_india.csv`).

From `TerraGuard/backend`, run:

```bash
ls -lh ../data/processed/nasa_landslides_india.csv
head -5 ../data/processed/nasa_landslides_india.csv
python - <<'PY'
import pandas as pd
p = "../data/processed/nasa_landslides_india.csv"
d = pd.read_csv(p)
print("rows:", len(d))
print("columns:", d.columns.tolist())
print(d[["event_date", "latitude", "longitude"]].head())
print("valid coordinates:", d.latitude.notna().sum(), d.longitude.notna().sum())
print("lat range:", d.latitude.min(), d.latitude.max())
print("lon range:", d.longitude.min(), d.longitude.max())
PY
```

If the file is missing or empty, acquire/normalize it:

```bash
python -m app.ml.real_data.download_catalog
```

Run that command from `TerraGuard/backend`. It writes the normalized India
subset to `TerraGuard/data/processed/nasa_landslides_india.csv`.

Restart Uvicorn after placing the file. Then inspect:

```bash
curl -s http://localhost:8000/health | python -m json.tool
curl -s "http://localhost:8000/api/v1/historical/assess?latitude=27.036&longitude=88.2627" | python -m json.tool
```

Health now reports `catalog_path`, `catalog_event_count`, and `catalog_error`.
If `catalog_event_count` is 0, the index cannot produce non-zero values.
If the count is positive but a query index is 0, no inventory events were
found within the selected radius (default 25 km). Try `radius_km=100` as a
diagnostic, not as a final universal setting.

The live assessment response also includes `historical_evidence` now.
