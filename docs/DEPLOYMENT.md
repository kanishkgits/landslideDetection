# Deployment guide

## Before deploying
Run the full local data pipeline and training first. Confirm:
- `data/processed/nasa_landslides_india.csv` exists
- `backend/app/ml/artifacts/terragaurd_event_model.joblib` exists
- `backend/app/ml/artifacts/metrics.json` exists
- `/health` reports `model_ready=true` and `catalog_ready=true`

The model artifact and processed India event CSV must be included in the deployment image/repository or fetched from persistent object storage during deployment. They are intentionally excluded from Git by default because generated datasets and model binaries should be versioned deliberately. If committing for a small portfolio deployment, force-add only the required files and document their source/version.

## Docker Compose
From project root, after local training:
```bash
docker compose up --build
```
- API: http://localhost:8000/docs
- Frontend: http://localhost:8080

## Render backend (manual)
1. Push the repository to GitHub.
2. Create a new Web Service in Render connected to the repository.
3. Runtime: Python.
4. Build command: `pip install -r backend/requirements.txt`
5. Start command: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Add environment variable `CORS_ORIGINS` with your deployed frontend origin.
7. Ensure `data/processed/nasa_landslides_india.csv` and `backend/app/ml/artifacts/` are present in the build context or fetched at startup from persistent storage.
8. Test `/health`, `/api/v1/events`, and `/api/v1/live/weather`.

## Vercel frontend (manual)
1. Import the repository into Vercel.
2. Set Root Directory to `frontend`.
3. Build command: `npm run build`.
4. Output directory: `dist`.
5. Set `VITE_API_URL` to the deployed backend base URL, including `https://`.
6. Redeploy after setting the environment variable.

## Production notes
- Use HTTPS, restrictive CORS, rate limits and API timeouts.
- Avoid running large data acquisition/training jobs inside web workers.
- Store model artifacts and data in versioned object storage or a persistent disk.
- Use a scheduled worker for ingestion; record source timestamps and staleness.
- Do not expose experimental scores as public alerts.
