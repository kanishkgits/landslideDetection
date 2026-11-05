# TerraGuard composite landslide screening score

The API returns `final_score.final_landslide_screening_score` on a 0-100
scale. It is a transparent heuristic research screening index, NOT a
calibrated probability, forecast, official warning or evacuation instruction.

Default component weights:
- Reported event count within 25 km: 30%
- Nearest reported event proximity: 20%
- Recency of newest nearby event: 10%
- Existing ML relative event score: 20%
- Recent rainfall accumulation: 15%
- Soil moisture: 5%

Missing components are omitted and remaining weights are renormalized.
The API exposes the component scores and weights so the dashboard can explain
each assessment. The historical count and distance terms intentionally make
places with more and closer reported landslides score higher, all else equal.

The rainfall scales and soil-moisture normalization are heuristic, not
locally calibrated thresholds. The ML model was trained on reported events
and pseudo-absence controls, so its output is not a probability. Elevation
is not independently weighted because it is not a reliable standalone
landslide predictor. Slope, geology, land cover, drainage, soil properties,
and a more complete NRSC/ISRO inventory should be added before scientific
validation. Do not use this prototype for public warnings or evacuation.
