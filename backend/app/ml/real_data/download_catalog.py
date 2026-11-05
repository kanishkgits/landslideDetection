"""Download NASA's public Global Landslide Catalog export and create India subset.

The NASA data.gov CSV export is a one-time export current through 2016-03-07.
For newer COOLR records, download an export from NASA Landslides/COOLR and pass
it with --input-csv. The script never fabricates events.
"""
import argparse
from pathlib import Path
import pandas as pd
import httpx

NASA_CSV = "https://data.nasa.gov/docs/legacy/Global_Landslide_Catalog_Export/Global_Landslide_Catalog_Export_rows.csv"

ALIASES = {
    "date": ["event_date", "date", "eventdate"],
    "latitude": ["latitude", "lat"],
    "longitude": ["longitude", "lon", "lng"],
    "country": ["country_name", "country", "countryname"],
}

def find_col(df, choices):
    lookup = {c.lower().strip().replace(" ", "_"): c for c in df.columns}
    for name in choices:
        if name in lookup:
            return lookup[name]
    return None

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--input-csv", help="Optional downloaded NASA COOLR/GLC CSV")
    p.add_argument("--raw-dir", default="../data/raw")
    p.add_argument("--out", default="../data/processed/nasa_landslides_india.csv")
    args = p.parse_args()
    raw_dir = Path(args.raw_dir); raw_dir.mkdir(parents=True, exist_ok=True)
    source = Path(args.input_csv) if args.input_csv else raw_dir / "nasa_global_landslide_catalog.csv"
    if not args.input_csv:
        print("Downloading NASA Global Landslide Catalog export...")
        with httpx.Client(timeout=120, follow_redirects=True) as client:
            r = client.get(NASA_CSV)
            r.raise_for_status()
            source.write_bytes(r.content)
    df = pd.read_csv(source, low_memory=False)
    date_col = find_col(df, ALIASES["date"])
    lat_col = find_col(df, ALIASES["latitude"])
    lon_col = find_col(df, ALIASES["longitude"])
    country_col = find_col(df, ALIASES["country"])
    missing = [n for n,c in [("date",date_col),("latitude",lat_col),("longitude",lon_col),("country",country_col)] if c is None]
    if missing:
        raise ValueError(f"Could not identify required fields {missing}. Available columns: {list(df.columns)}")
    out = pd.DataFrame({
        "event_date": pd.to_datetime(df[date_col], errors="coerce", utc=True).dt.strftime("%Y-%m-%d"),
        "latitude": pd.to_numeric(df[lat_col], errors="coerce"),
        "longitude": pd.to_numeric(df[lon_col], errors="coerce"),
        "country": df[country_col].astype(str).str.strip()
    })
    out["source_record_id"] = df.index.astype(str)
    out = out[out.country.str.casefold().isin(["india", "in"])].copy()
    out = out.dropna(subset=["event_date","latitude","longitude"])
    out = out[out.latitude.between(6.0, 37.5) & out.longitude.between(68.0, 98.0)]
    out = out.drop_duplicates(subset=["event_date","latitude","longitude"])
    dest = Path(args.out); dest.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(dest, index=False)
    print(f"India events: {len(out):,}")
    print(f"Date range: {out.event_date.min() if len(out) else 'n/a'} to {out.event_date.max() if len(out) else 'n/a'}")
    print(f"Saved: {dest.resolve()}")
    if len(out) < 30:
        print("WARNING: Few India records. Consider obtaining a newer COOLR export or the NRSC/Bhuvan inventory.")
    print("Source: NASA Global Landslide Catalog export. Its static data.gov export ends 2016-03-07.")

if __name__ == "__main__": main()
