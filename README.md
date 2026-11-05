# TerraGuard — India Landslide Research & Monitoring System

TerraGuard is a software-only end-to-end research prototype. It combines:
- NASA Global Landslide Catalog (reported landslide events; static data.gov export through 2016-03-07)
- Open-Meteo historical ERA5 reanalysis (rainfall and soil moisture features)
- Open-Meteo live forecast/recent-hourly API for location assessments
- Scikit-learn Random Forest research classifier
- FastAPI backend
- React + Leaflet dashboard

**Critical limitations:** This is not a certified warning system. The model is trained to distinguish NASA-reported events from spatially displaced pseudo-absence samples. Pseudo-absence points are not verified non-landslide observations. The model output is a relative event-discrimination score, not a calibrated probability. NASA's static CSV is dated; obtain a newer COOLR export if available. NRSC/ISRO's richer India inventory is exposed through Bhuvan and may require portal/service access; it is not silently scraped here.

## 1. Requirements
- Python 3.10+
- Node.js 18+
- Internet connection for dataset/weather APIs

## 2. Backend installation
```bash
cd backend
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Download real landslide inventory
From `backend/`:
```bash
python -m app.ml.real_data.download_catalog
```
This downloads NASA's public Global Landslide Catalog export, filters India records and writes:
`data/processed/nasa_landslides_india.csv`

If you have a newer NASA COOLR CSV export:
```bash
python -m app.ml.real_data.download_catalog --input-csv /path/to/coolr_export.csv
```

The NASA data.gov static export is current only through 2016-03-07. The NASA catalog includes media, disaster-database and scientific-report records; reporting coverage is uneven. See source notes below.

## 4. Enrich event/control points with real weather reanalysis
```bash
python -m app.ml.real_data.build_training_data --max-events 250
```
This queries Open-Meteo ERA5 historical hourly precipitation and soil moisture for the seven complete days before each catalog event. It creates one spatially displaced, date-matched background point for each event. API responses are cached in `data/cache/open_meteo/` to avoid repeat calls.

Output:
`data/processed/india_event_case_control.csv`

Use `--max-events 30` for a small initial run. Increase after confirming the pipeline and provider usage limits.

## 5. Train the model
```bash
python -m app.ml.real_data.train_model
```
Artifact:
`backend/app/ml/artifacts/terragaurd_event_model.joblib`

Metrics:
`backend/app/ml/artifacts/metrics.json`

The split keeps matched event/control pairs together using `GroupShuffleSplit`. This is better than a row-random split, but it is not a spatially independent or temporally independent test. Do not present metrics as generalization to unseen districts or future monsoons.

## 6. Start the API
From `backend/`:
```bash
uvicorn app.main:app --reload
```
Docs: http://127.0.0.1:8000/docs

Endpoints:
- `GET /health`
- `GET /api/v1/events?limit=1500`
- `GET /api/v1/model/metrics`
- `GET /api/v1/live/weather?latitude=30.3&longitude=79.0`
- `POST /api/v1/live/assess` with `{"latitude":30.3,"longitude":79.0}`

## 7. Start the frontend
New terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

Set `VITE_API_URL` if backend is not at `http://localhost:8000`.

## 8. Data sources and provenance
- NASA Global Landslide Catalog: https://catalog.data.gov/dataset/global-landslide-catalog-export-75464
  - Static export: https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv
  - NASA notes this one-time export is current through March 7, 2016.
- NASA/NRSC Landslide Atlas: https://www.nrsc.gov.in/nrscnew/resources_atlas_landslide.php
  - Approximately 80,000 mapped landslides across 17 states and 2 UTs, 1998–2022; not uniform national coverage. Access geospatial layers through official Bhuvan/NRSC channels.
- Open-Meteo Historical Weather API: https://open-meteo.com/en/docs/historical-weather-api
  - ERA5 reanalysis is modelled/reanalysis weather, not a local rain gauge observation.
- Open-Meteo Forecast API: https://open-meteo.com/en/docs
  - Used for recent hourly/forecast inputs in live location assessments.
- Copernicus DEM: https://registry.opendata.aws/copernicus-dem/
  - A future terrain-feature integration; current model uses Open-Meteo elevation metadata.

## 9. Reproducibility
Save downloaded raw files, generated processed CSVs, metrics and model artifact with source/version/date metadata. The pipeline caches API responses. Do not commit large raw datasets or secrets. See `.gitignore`.

## 10. Research validation needed before operational use
- Obtain current NRSC/GSI/Bhuvan event inventory and stable event IDs.
- Build true non-event observations from complete monitoring windows, not arbitrary unlabeled cells.
- Include spatial terrain covariates (slope, lithology, land cover, drainage distance).
- Use blocked spatial validation by district/region and temporal holdout by monsoon/year.
- Calibrate probabilities and report PR-AUC, recall, precision, Brier score, false alarms per region/time and lead time.
- Compare with official rainfall thresholds and NASA LHASA/official hazard products where appropriate.
- Have domain experts review all warnings. This prototype must not direct evacuations.

## 11. Deployment
See `docs/DEPLOYMENT.md`. Docker Compose files are included for a local containerized run. For Render/Vercel, deploy backend and frontend separately and make sure the trained model artifact plus processed event CSV are included or fetched from persistent storage.
\n\n## Historical occurrence evidence (new)\n\nSee [Historical Evidence](docs/HISTORICAL_EVIDENCE.md). The dashboard now displays a distance-weighted historical reported-event index separately from the ML relative event score. It increases with nearby recorded events; it is not a probability and zero means no records in the loaded inventory, not zero hazard.\n