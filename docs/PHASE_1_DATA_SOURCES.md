# Phase 1 source acquisition checklist

## 1. Landslide inventory
NRSC/ISRO reports approximately 80,000 mapped landslides for 1998–2022 across 17 states and 2 UTs, including seasonal, event-based and route-wise inventories. Its seasonal inventory includes 2014 and 2017 rainy-season pan-India inventories. Coverage and completeness are not uniform. Read the atlas/source metadata and obtain the actual geospatial files through the official NRSC route. Do not scrape map images and treat pixels as point records.

Official page: https://www.nrsc.gov.in/nrscnew/resources_atlas_landslide.php

## 2. Rainfall
NASA GPM IMERG provides half-hourly precipitation estimates on a 0.1-degree grid. Early Run is designed for low latency (roughly four hours); Late Run is roughly fourteen hours; Final Run is gauge-adjusted and available after a longer processing delay. The variable may be a rate (mm/hr) or an accumulation (mm); inspect product metadata and units before deriving rolling totals.

Official pages:
- https://gpm.nasa.gov/data/imerg
- https://gpm.nasa.gov/data/directory
- https://gpm.nasa.gov/resources/documents/imerg-v07-technical-documentation

## 3. Elevation
Copernicus DEM GLO-30 and GLO-90 are global elevation products. Current access conditions for GLO-30 may require Copernicus Contributing Missions registration; GLO-90 is a practical fallback. Keep native resolution and vertical datum metadata.

Official pages:
- https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- https://documentation.dataspace.copernicus.eu/Data/Others/CCM.html

## 4. Data provenance columns
For every source-derived record, preserve: `source`, `product`, `version`, `downloaded_at`, `observation_time`, `spatial_resolution`, `temporal_resolution`, `units`, `quality_flag`, `license_or_terms`, and source file checksum.

## 5. Current limitation
The first preprocessing script creates an India grid, marks inventory intersections, and samples elevation. It does not yet calculate slope, rainfall windows, or a temporally valid event target. Those must be implemented after obtaining source rasters and understanding their metadata.
