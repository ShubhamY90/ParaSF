#!/bin/bash
# setup_data.sh — Run this ONCE before the hackathon to fetch ERA5 data.
#
# Usage:
#   cd ParaSF/backend
#   bash scripts/setup_data.sh
#
# What it does:
#   1. Installs required Python packages
#   2. Downloads ERA5 rainfall data from Copernicus CDS (needs internet)
#   3. Processes it into era5_rainfall.json used by the simulation engine

set -e

PYTHON=${PYTHON:-python3}

echo ""
echo "=== ParaTrust Data Setup ==="
echo ""

# 1. Install packages
echo "[1/3] Installing Python packages..."
$PYTHON -m pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org \
  cdsapi xarray scipy "netCDF4>=1.6" numpy pandas lightgbm scikit-learn \
  2>&1 | grep -E "Successfully|already satisfied|error" | head -20

echo ""

# 2. Create data dir
mkdir -p data
echo "[2/3] Fetching ERA5 rainfall data from Copernicus CDS..."
$PYTHON scripts/fetch_era5_rainfall.py

echo ""

# 3. Done
echo "[3/3] Done! era5_rainfall.json is ready."
echo "      The simulation engine will use real ERA5 data automatically."
echo ""
