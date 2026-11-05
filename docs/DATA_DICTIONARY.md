# TerraGuard data dictionary

## Observation grain
One record should represent one location (or raster cell) at one observation time and one explicitly defined forecast horizon.

## Required model fields
| Field | Unit | Meaning |
|---|---|---|
| rain_1h_mm | mm | Accumulated rainfall in preceding hour |
| rain_24h_mm | mm | Accumulated rainfall in preceding 24 hours |
| rain_72h_mm | mm | Accumulated rainfall in preceding 72 hours |
| rain_7d_mm | mm | Accumulated rainfall in preceding 7 days |
| slope_deg | degrees | Terrain slope |
| elevation_m | metres | Elevation |
| soil_moisture_pct | % | Volumetric or product-specific soil moisture; document source/definition |
| landslide | 0/1 | Verified event label for defined forecast horizon |

## Required provenance fields for real data
`source`, `source_product`, `source_version`, `observed_at`, `ingested_at`, `latitude`, `longitude`, `spatial_resolution`, `temporal_resolution`, `quality_flag`, `label_source`, `event_id`, `forecast_horizon`.

Never mix rainfall rate (mm/hour) with rainfall accumulation (mm) without explicit conversion. Preserve nodata values and quality flags.
