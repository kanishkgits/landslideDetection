import argparse
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from shapely.geometry import box

EQUAL_AREA_CRS = "EPSG:6933"

def make_grid(boundary: gpd.GeoDataFrame, grid_m: int) -> gpd.GeoDataFrame:
    geom = boundary.geometry.union_all()
    minx, miny, maxx, maxy = geom.bounds
    xs = np.arange(minx, maxx, grid_m)
    ys = np.arange(miny, maxy, grid_m)
    cells = []
    ids = []
    idx = 0
    for x in xs:
        for y in ys:
            cell = box(x, y, x + grid_m, y + grid_m)
            if cell.intersects(geom):
                cells.append(cell.intersection(geom))
                ids.append(f"IN-{idx:07d}")
                idx += 1
    grid = gpd.GeoDataFrame({"grid_id": ids}, geometry=cells, crs=EQUAL_AREA_CRS)
    grid = grid[~grid.geometry.is_empty].copy()
    grid["centroid"] = grid.geometry.centroid
    return grid

def main():
    p = argparse.ArgumentParser(description="Build India grid + landslide inventory presence/background dataset.")
    p.add_argument("--boundary", required=True, help="India boundary GeoJSON")
    p.add_argument("--inventory", required=True, help="Landslide inventory GeoJSON")
    p.add_argument("--dem", required=True, help="Projected DEM GeoTIFF")
    p.add_argument("--out", default="data/processed/india_susceptibility_presence_background.csv")
    p.add_argument("--grid-km", type=float, default=5.0)
    args = p.parse_args()

    boundary = gpd.read_file(args.boundary)
    inventory = gpd.read_file(args.inventory)
    if boundary.empty or inventory.empty:
        raise ValueError("Boundary and inventory must both contain features.")
    if boundary.crs is None or inventory.crs is None:
        raise ValueError("Both vector files must declare a CRS.")
    if args.grid_km <= 0:
        raise ValueError("--grid-km must be positive.")

    boundary = boundary.to_crs(EQUAL_AREA_CRS)
    inventory = inventory.to_crs(EQUAL_AREA_CRS)
    boundary_geom = boundary.geometry.union_all()
    inventory = inventory[inventory.geometry.notna() & ~inventory.geometry.is_empty].copy()
    inventory = inventory[inventory.intersects(boundary_geom)]
    grid = make_grid(boundary, int(args.grid_km * 1000))

    # Spatial presence: count inventory geometries intersecting each cell.
    joined = gpd.sjoin(grid[["grid_id", "geometry"]], inventory[["geometry"]],
                       how="left", predicate="intersects")
    counts = joined.groupby("grid_id")["index_right"].count().rename("inventory_feature_count")
    grid = grid.merge(counts, on="grid_id", how="left")
    grid["inventory_feature_count"] = grid["inventory_feature_count"].fillna(0).astype(int)
    grid["inventory_presence"] = (grid["inventory_feature_count"] > 0).astype(int)

    # Sample DEM at cell centroids in the DEM's native coordinate reference system.
    with rasterio.open(args.dem) as src:
        if src.crs is None:
            raise ValueError("DEM must have a CRS.")
        centroids = gpd.GeoSeries(grid["centroid"], crs=EQUAL_AREA_CRS).to_crs(src.crs)
        coords = [(pt.x, pt.y) for pt in centroids]
        sampled = np.array([v[0] for v in src.sample(coords, masked=True)], dtype="float64")
        nodata = src.nodata
        if nodata is not None:
            sampled[sampled == nodata] = np.nan
        sampled[(sampled < -500) | (sampled > 9000)] = np.nan
        grid["elevation_m"] = sampled

    # Coordinates for mapping, in WGS84.
    cent_wgs = gpd.GeoSeries(grid["centroid"], crs=EQUAL_AREA_CRS).to_crs("EPSG:4326")
    grid["longitude"] = cent_wgs.x
    grid["latitude"] = cent_wgs.y
    grid["grid_km"] = args.grid_km
    grid["label_definition"] = "INVENTORY_PRESENCE_NOT_EVENT_PROBABILITY"
    grid["inventory_source"] = Path(args.inventory).name

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    cols = ["grid_id", "latitude", "longitude", "grid_km", "elevation_m",
            "inventory_feature_count", "inventory_presence", "label_definition",
            "inventory_source"]
    grid[cols].to_csv(out, index=False)
    print(f"Saved {len(grid):,} grid cells to {out}")
    print(f"Cells with inventory presence: {int(grid.inventory_presence.sum()):,}")
    print(f"Cells without mapped inventory: {int((grid.inventory_presence == 0).sum()):,}")
    print("WARNING: absence from this inventory is not proof of no landslide.")

if __name__ == "__main__":
    main()
