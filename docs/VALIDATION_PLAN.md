# Validation plan

1. Define target: e.g. documented landslide occurrence in a grid cell within the next 24 hours.
2. Build positive samples from dated, geolocated inventory events.
3. Build negative samples only from locations/times with adequate observation coverage and no recorded event; account for incomplete inventories.
4. Join rainfall windows that end before prediction time; prevent future-data leakage.
5. Split by geography and time (spatial blocks + held-out monsoon seasons/events).
6. Report PR-AUC, recall, precision, calibration, Brier score, false alarms per region/time, and lead time.
7. Compare against simple rainfall thresholds and published external nowcasts.
8. Calibrate probabilities on held-out data; do not call raw model scores probabilities.
9. Audit performance by state, terrain class, season and data availability.
10. Document uncertainty and abstain when inputs are stale or missing.
