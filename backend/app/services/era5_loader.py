"""
era5_loader.py — Stage 4/6 helper.

Loads the pre-fetched ERA5 rainfall JSON (produced by fetch_era5_rainfall.py)
and provides two interfaces used by the simulation engine and risk service:

  get_base_signal(tick)      → mean_mm_hr for that tick (float)
  get_grid_at_tick(tick)     → list of (lon, lat, mm_hr) for spatial use

Falls back to a synthetic Gaussian curve if the JSON file is absent, so the
app works even before ERA5 data is fetched.
"""
from __future__ import annotations

import json
import math
import pathlib
from functools import lru_cache

_JSON_PATH = pathlib.Path(__file__).parent.parent.parent / "data" / "era5_rainfall.json"


@lru_cache(maxsize=1)
def _load() -> dict | None:
    if _JSON_PATH.exists():
        try:
            return json.loads(_JSON_PATH.read_text())
        except Exception:
            return None
    return None


def _synthetic_signal(tick: int, total_ticks: int = 72) -> float:
    """Gaussian storm pulse centred at mid-scenario — used as fallback."""
    t = tick / max(total_ticks - 1, 1)
    base = 0.5
    storm = 25.0 * math.exp(-0.5 * ((t - 0.5) / 0.18) ** 2)
    return base + storm


def get_base_signal(tick: int) -> float:
    """Return mm/hr area-mean rainfall for the given tick.

    Uses real ERA5 data when available; falls back to synthetic otherwise.
    Tick indices wrap around if the scenario runs longer than the ERA5 data.
    """
    data = _load()
    if data is None:
        return _synthetic_signal(tick)
    n = data.get("n_ticks", 72)
    key = str(tick % n)
    tick_data = data.get("ticks", {}).get(key, {})
    return tick_data.get("mean_mm_hr", _synthetic_signal(tick))


def get_max_signal(tick: int) -> float:
    """Return mm/hr area-max rainfall for the given tick."""
    data = _load()
    if data is None:
        return _synthetic_signal(tick) * 2.5
    n = data.get("n_ticks", 72)
    key = str(tick % n)
    tick_data = data.get("ticks", {}).get(key, {})
    return tick_data.get("max_mm_hr", _synthetic_signal(tick) * 2.5)


def get_grid_at_tick(tick: int) -> list[tuple[float, float, float]]:
    """Return list of (lon, lat, mm_hr) grid points for spatial interpolation.

    Used by Stage 6 (GP/Kriging) to blend ERA5 raster signal with gauge readings.
    Returns empty list if ERA5 data not available.
    """
    data = _load()
    if data is None:
        return []
    n = data.get("n_ticks", 72)
    key = str(tick % n)
    raw = data.get("ticks", {}).get(key, {}).get("grid_values", [])
    return [(r[0], r[1], r[2]) for r in raw]


def era5_available() -> bool:
    """True when real ERA5 data is loaded (not synthetic fallback)."""
    return _load() is not None
