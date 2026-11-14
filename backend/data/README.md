# ParaTrust Data Layer

## Quick Start (run once before hackathon)

```bash
cd ParaSF/backend

# Option A — simple
bash scripts/setup_data.sh

# Option B — manual
pip install cdsapi xarray scipy netCDF4
python3 scripts/fetch_era5_rainfall.py
```

## What gets generated

| File | What |
|------|------|
| `data/era5_rainfall.nc` | Raw ERA5 NetCDF (kept for audit) |
| `data/era5_rainfall.json` | Per-tick rainfall signal used by simulation |

## ERA5 Event

**Aug 18–20, 2021 — Uttar Pradesh excess rainfall event**
- District: Varanasi / Kashi-Ganga demo area
- Variable: `total_precipitation` (ERA5-Land, hourly)
- 72 ticks (3 days × 24 hours)

## Fallback

If ERA5 data is not fetched, the simulation automatically falls back to a
synthetic Gaussian storm pulse. The app works either way — ERA5 just makes
the base signal physically realistic.

## Sensor fault classifier

The LightGBM model trains on startup (cached). Two new features added:

- `satellite_wet_flag` — 1 when satellite shows wet pixel (genuine cell only)
- `storm_proximity` — 1 when storm track passes near (genuine cell only)

These are what separate `genuine_localised_cell` from `spike` at inference time.
Pass them via `satellite_wet_ids` and `storm_cell_ids` to `classify_readings()`.

## CDS Credentials

```
url: https://cds.climate.copernicus.eu/api
key: 7d7d576d-a418-4edf-8eae-892440b4a1ef
```
Credentials are embedded in `fetch_era5_rainfall.py` — no manual setup needed.
