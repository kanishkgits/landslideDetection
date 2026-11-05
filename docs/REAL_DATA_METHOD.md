# TerraGuard real-data method and limitations

## Training target
`landslide_reported=1`: a NASA Global Landslide Catalog record.
`landslide_reported=0`: a randomly displaced point 12–25 km away, at the same event date, used as a matched background/pseudo-absence sample.

This is a case-control discrimination experiment. It does not establish that the control point was landslide-free. NASA's catalog is based on reports and is affected by media/reporting bias and location uncertainty. The public data.gov export is a one-time export current through 2016-03-07.

## Weather features
Open-Meteo Archive API, ERA5 model, hourly precipitation (mm per preceding hour) and soil moisture. Seven complete days before the event date are used; the event date itself is excluded to reduce timestamp ambiguity. Rainfall sums are computed over preceding 24, 72 and 168 hours. Soil moisture is averaged over the final 24 hours and converted from m³/m³ to percent.

## Live scoring
Open-Meteo Forecast API provides the recent 7-day hourly window and upcoming forecast. Features are computed in the same units. The trained model returns a relative event-discrimination score. Because training uses pseudo-absences and catalog-reporting labels, this score is not a probability of a landslide at the queried location.

## Known gaps
- India catalog subset may be sparse, especially for remote areas.
- NRSC/ISRO inventory is richer but its downloadable geospatial access may require Bhuvan portal/service permissions.
- Model currently lacks slope, lithology, land cover and road/river distance.
- Open-Meteo ERA5 grid is coarse (~25 km), not a slope-scale rainfall sensor.
- Spatially displaced controls are imperfect and can contain unreported landslides.
