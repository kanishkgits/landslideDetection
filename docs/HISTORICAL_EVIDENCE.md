# Historical reported-event evidence

TerraGuard now exposes a distinct **Historical Occurrence Index (0–100)**.
It is calculated from the distance-weighted density of catalogued landslide
coordinates around a query point (default radius 25 km). Each recorded event
contributes more when closer to the query point. Consequently, additional
nearby reported events increase the index. This is an inventory-evidence
indicator, not a probability, calibrated susceptibility estimate, or official
hazard class.

API:
- `GET /api/v1/historical/assess?latitude=27.036&longitude=88.2627&radius_km=25`
- `POST /api/v1/live/assess` now includes `historical_evidence` alongside the
  separate ML relative event score and weather features.

Important limitations:
- The NASA static export is a historical snapshot and is not a complete India
  landslide inventory. Newer NASA COOLR/NRSC records can be incorporated by
  importing a verified CSV with the supported `--input-csv` option.
- A zero index means no records were found in the loaded inventory, not that
  the location is safe or has never experienced a landslide.
- Event density is affected by reporting, access, population, and observation
  bias. A dense cluster may partly reflect better reporting.
- This index should not be displayed as "landslide probability".
- The live ML score remains a relative classifier score trained on an
  event-vs-pseudo-absence dataset and is not calibrated probability.
- Historical event density does not replace slope, geology, land cover,
  drainage, or field verification.

The frontend deliberately displays historical evidence and ML score in
separate panels so users cannot confuse them.
