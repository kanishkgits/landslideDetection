# Phase 1: geospatial susceptibility dataset

This pipeline builds a **spatial presence/background research table**, not a calibrated event-probability dataset.

## Inputs
1. India land boundary GeoJSON in a projected CRS suitable for distance/grid work (or use an equal-area projection during processing).
2. Landslide inventory GeoJSON with event geometries.
3. DEM GeoTIFF with elevation in metres and a projected CRS.

The inventory schema must have valid geometries. Preserve available event date, source ID and inventory type fields. The script uses the geometry intersection with grid cells to mark presence.

## Install
```bash
pip install geopandas rasterio shapely pyproj pandas numpy
```

## Run
```bash
python -m app.ml.data_pipeline.build_susceptibility_dataset \
  --boundary data/raw/india_boundary.geojson \
  --inventory data/raw/landslide_inventory.geojson \
  --dem data/raw/copernicus_dem_india.tif \
  --out data/processed/india_susceptibility_presence_background.csv \
  --grid-km 5
```

The script reprojects all vector inputs into a local metric CRS (EPSG:6933 equal-area), creates grid-cell centroids, marks cells intersecting inventory geometries, and samples elevation from the DEM. DEM sampling is performed in the DEM's native CRS.

## Critical interpretation
- `inventory_presence=1` means at least one mapped inventory geometry intersects the cell.
- `inventory_presence=0` means no mapped inventory geometry was found; it does **not** establish that the cell is landslide-free.
- This output is suitable for exploratory susceptibility mapping and data QA. Do not feed it directly into a supervised classifier and report its output as a real landslide probability.
- For a defensible classifier, construct documented background samples, account for inventory incompleteness and spatial sampling bias, and validate with spatially blocked holdouts.
- The DEM is sampled at cell centroids in this first version. Slope, curvature, lithology, land cover, soil and distance-to-drainage are later feature-engineering tasks.
