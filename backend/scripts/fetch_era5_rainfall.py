"""
fetch_era5_rainfall.py — Stage 4 real data layer.

Downloads hourly ERA5-Land total_precipitation for the Vidarbha (Nagpur/Wardha)
demo district for the July 2022 monsoon excess rainfall event (a real, well-documented
high-rainfall flood event in Vidarbha).

Output
------
  backend/data/era5_rainfall.nc       — raw NetCDF from CDS
  backend/data/era5_rainfall.json     — preprocessed per-tick gauge-level
                                        signal used by the simulation engine

The JSON is what the simulation engine reads; the NC file is kept for audit.

Usage
-----
  python3 scripts/fetch_era5_rainfall.py

Requires
--------
  pip install cdsapi xarray scipy netCDF4

CDS credentials are read from ~/.cdsapirc (auto-created by this script on
first run from the env-vars below, so you don't need to manually create it).
"""

import json
import os
import pathlib
import sys

# ── CDS credentials (injected here so team doesn't need to manage ~/.cdsapirc) ─
CDS_URL = "https://cds.climate.copernicus.eu/api"
CDS_KEY = "7d7d576d-a418-4edf-8eae-892440b4a1ef"

# ── Target event: Vidarbha / Nagpur region, July 2022 excess rainfall event ──
EVENT_YEAR  = "2022"
EVENT_MONTH = "07"
EVENT_DAYS  = ["12", "13", "14"]   # 3-day peak monsoon flood event

# Bounding box for the Vidarbha demo district (N/W/S/E for CDS API)
# CDS uses [North, West, South, East]
BBOX_CDS = [21.270, 78.950, 21.020, 79.230]

# Output paths
DATA_DIR = pathlib.Path(__file__).parent.parent / "data"
NC_PATH   = DATA_DIR / "era5_rainfall.nc"
JSON_PATH = DATA_DIR / "era5_rainfall.json"


def write_cdsapirc():
    """Write ~/.cdsapirc so cdsapi can authenticate."""
    rc = pathlib.Path.home() / ".cdsapirc"
    if not rc.exists():
        rc.write_text(f"url: {CDS_URL}\nkey: {CDS_KEY}\n")
        print(f"[fetch_era5] Created {rc}")
    else:
        print(f"[fetch_era5] {rc} already exists, skipping overwrite.")


def download_era5():
    """Download ERA5-Land hourly precipitation to era5_rainfall.nc."""
    import cdsapi  # noqa: PLC0415

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if NC_PATH.exists():
        print(f"[fetch_era5] {NC_PATH} already exists — skipping download.")
        return

    print("[fetch_era5] Connecting to Copernicus CDS …")
    c = cdsapi.Client(url=CDS_URL, key=CDS_KEY, quiet=False)
    c.retrieve(
        "reanalysis-era5-land",
        {
            "variable":     ["total_precipitation"],
            "year":         EVENT_YEAR,
            "month":        EVENT_MONTH,
            "day":          EVENT_DAYS,
            "time":         [f"{h:02d}:00" for h in range(24)],
            "area":         BBOX_CDS,
            "format":       "netcdf",
        },
        str(NC_PATH),
    )
    print(f"[fetch_era5] Downloaded → {NC_PATH}")


def process_to_json():
    """
    Convert the NetCDF to a JSON dict keyed by tick (0-based hour index).
    If the downloaded file is a zip archive, extracts the .nc file first.
    """
    import numpy as np
    import xarray as xr  # noqa: PLC0415
    import zipfile

    actual_nc = NC_PATH
    if zipfile.is_zipfile(NC_PATH):
        print(f"[fetch_era5] {NC_PATH} is a zip archive. Extracting .nc file …")
        with zipfile.ZipFile(NC_PATH, "r") as z:
            nc_files = [f for f in z.namelist() if f.endswith(".nc")]
            if not nc_files:
                raise ValueError("No .nc file found in downloaded zip archive.")
            extracted_path = DATA_DIR / nc_files[0]
            z.extract(nc_files[0], path=DATA_DIR)
            actual_nc = extracted_path
            print(f"[fetch_era5] Extracted → {actual_nc}")

    print(f"[fetch_era5] Processing {actual_nc} …")
    ds = xr.open_dataset(actual_nc)

    # ERA5 uses 'tp' for total precipitation (m / hour)
    tp_var = "tp" if "tp" in ds else list(ds.data_vars)[0]
    tp = ds[tp_var]

    # Coordinates may be 'latitude'/'longitude' or 'lat'/'lon'
    lat_dim = "latitude" if "latitude" in tp.dims else "lat"
    lon_dim = "longitude" if "longitude" in tp.dims else "lon"
    time_dim = "time" if "time" in tp.dims else tp.dims[0]

    lats = tp[lat_dim].values.tolist()
    lons = tp[lon_dim].values.tolist()

    ticks = {}
    for tick_idx, t in enumerate(tp[time_dim].values):
        slice_ = tp.sel({time_dim: t})
        vals_m_hr = slice_.values  # shape: (lat, lon)
        vals_mm_hr = vals_m_hr * 1000.0  # m → mm

        # Flatten to list of [lon, lat, mm_hr] for spatial use
        grid = []
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                v = float(vals_mm_hr[i, j])
                if v > 0.001:   # skip dry cells to keep JSON small
                    grid.append([round(lon, 4), round(lat, 4), round(v, 4)])

        ticks[str(tick_idx)] = {
            "mean_mm_hr": round(float(np.nanmean(vals_mm_hr)), 4),
            "max_mm_hr":  round(float(np.nanmax(vals_mm_hr)), 4),
            "grid_values": grid,
        }

    out = {
        "source":    "ERA5-Land reanalysis, Copernicus CDS",
        "event":     f"Vidarbha Excess Rainfall {EVENT_YEAR}-{EVENT_MONTH} (days {EVENT_DAYS})",
        "bbox":      [78.950, 21.020, 79.230, 21.270],
        "n_ticks":   len(ticks),
        "ticks":     ticks,
    }

    JSON_PATH.write_text(json.dumps(out, indent=2))
    print(f"[fetch_era5] JSON written → {JSON_PATH}  ({len(ticks)} ticks)")


if __name__ == "__main__":
    write_cdsapirc()
    try:
        download_era5()
    except Exception as e:
        print(f"[fetch_era5] ERROR during download: {e}", file=sys.stderr)
        print("[fetch_era5] Tip: check your CDS key and ensure you've accepted "
              "the ERA5-Land licence at cds.climate.copernicus.eu/datasets", file=sys.stderr)
        sys.exit(1)
    process_to_json()
    print("[fetch_era5] Done.")
