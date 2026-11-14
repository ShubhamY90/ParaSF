"""Stage 3 geospatial service.

Pure-Python geographic helpers — no heavy geospatial dependencies required for
rendering polygons and markers on the map. Real geospatial processing (Kriging,
Gaussian Process spatial estimation) arrives in Stage 6, where GeoPandas / Shapely
are justified.

This module owns the *simulated* geographic context for the demo district:
  - the demo district boundary
  - rainfall / water-level gauge (sensor) locations
  - rivers and water bodies
  - deterministic generation from ``settings.simulation_seed`` so the same demo
    scenario is reproducible (a foundation Stage 4 builds on).

Farm records themselves come from the database (Stage 2); this service only
generates a boundary polygon around a farm centroid when the farm has no stored
``boundary_geojson``.
"""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from typing import Any

from app.core.config import settings

# ─── Demo district definition ────────────────────────────────────────────────
# Centred on the Varanasi / Ganga basin area. Coordinates are (lat, lng).
DEMO_DISTRICT_NAME = "Kashi-Ganga Demo District"
DEMO_DISTRICT_CENTRE = (25.335, 82.965)

# Bounding box used for fast "is this farm inside the demo district?" filtering.
# Stored as (min_lng, min_lat, max_lng, max_lat).
DEMO_DISTRICT_BBOX: tuple[float, float, float, float] = (82.835, 25.205, 83.095, 25.465)

# An irregular (but simple) polygon enclosing the demo district. [lng, lat] pairs,
# closed (first == last). Clearly a *simulated* boundary — not an administrative
# cadastre.
DEMO_DISTRICT_POLYGON: list[list[float]] = [
    [82.845, 25.225],
    [82.960, 25.210],
    [83.085, 25.230],
    [83.100, 25.345],
    [83.005, 25.460],
    [82.870, 25.455],
    [82.835, 25.340],
    [82.845, 25.225],  # close the ring
]

# ─── Conversions ─────────────────────────────────────────────────────────────

# Approx metres per degree (good enough for farm-scale polygons at this latitude).
_M_PER_DEG_LAT = 111_320.0


def _m_per_deg_lng(lat: float) -> float:
    return _M_PER_DEG_LAT * math.cos(math.radians(lat))


def farm_centroid_square(lat: float, lng: float, area_hectares: float | None) -> list[list[float]]:
    """Return a square polygon ([lng, lat] pairs, closed) centred on a farm centroid.

    Sized from the farm area. Falls back to a ~1.5 ha square when area is unknown.
    """
    ha = area_hectares if area_hectares and area_hectares > 0 else 1.5
    side_m = math.sqrt(ha * 10_000.0)  # 1 ha == 10000 m^2
    half_lat = (side_m / 2.0) / _M_PER_DEG_LAT
    half_lng = (side_m / 2.0) / _m_per_deg_lng(lat)
    return [
        [lng - half_lng, lat - half_lat],
        [lng + half_lng, lat - half_lat],
        [lng + half_lng, lat + half_lat],
        [lng - half_lng, lat + half_lat],
        [lng - half_lng, lat - half_lat],  # close
    ]


def parse_stored_boundary(boundary_geojson: str | None) -> dict | None:
    """Return a parsed GeoJSON geometry dict if ``boundary_geojson`` is a valid
    Polygon/MultiPolygon feature or geometry, else ``None``."""
    if not boundary_geojson:
        return None
    try:
        data = json.loads(boundary_geojson)
    except (json.JSONDecodeError, TypeError):
        return None
    # Accept either a bare geometry or a Feature.
    if isinstance(data, dict):
        if data.get("type") in ("Polygon", "MultiPolygon"):
            return data
        geom = data.get("geometry")
        if isinstance(geom, dict) and geom.get("type") in ("Polygon", "MultiPolygon"):
            return geom
    return None


def farm_geometry(lat: float | None, lng: float | None, area_hectares: float | None,
                  boundary_geojson: str | None) -> dict | None:
    """Build a GeoJSON geometry for a farm.

    Priority: stored ``boundary_geojson`` → square polygon around the centroid.
    Returns ``None`` when the farm has no usable coordinates and no stored
    boundary (the farm is then omitted from the map layer).
    """
    stored = parse_stored_boundary(boundary_geojson)
    if stored:
        return stored
    if lat is None or lng is None:
        return None
    ring = farm_centroid_square(lat, lng, area_hectares)
    return {"type": "Polygon", "coordinates": [ring]}


def in_district(lat: float | None, lng: float | None) -> bool:
    """True when a point falls inside the demo district bounding box."""
    if lat is None or lng is None:
        return False
    min_lng, min_lat, max_lng, max_lat = DEMO_DISTRICT_BBOX
    return min_lng <= lng <= max_lng and min_lat <= lat <= max_lat


# ─── Simulated geographic features (deterministic from seed) ─────────────────

@dataclass
class Sensor:
    id: str
    name: str
    sensor_type: str  # "rainfall" | "water_level"
    latitude: float
    longitude: float
    simulated: bool = True
    status: str = "normal"  # Stage 5 populates this dynamically


@dataclass
class WaterFeature:
    id: str
    name: str
    kind: str  # "river" | "water_body"
    geometry: dict  # GeoJSON geometry
    simulated: bool = True


# The Ganga flows roughly south-easterly through the Varanasi area.
_RIVER_PATH: list[list[float]] = [
    [82.850, 25.405],
    [82.900, 25.380],
    [82.940, 25.355],
    [82.972, 25.335],
    [83.000, 25.315],
    [83.030, 25.290],
    [83.058, 25.265],
    [83.085, 25.240],
]


def _water_bodies() -> list[tuple[float, float, float]]:
    """Fixed demo water bodies (pond/lake centres + radius in degrees)."""
    return [
        (25.380, 82.905, 0.012),
        (25.290, 83.020, 0.009),
        (25.245, 82.890, 0.007),
    ]


def generate_sensors(seed: int | None = None) -> list[Sensor]:
    """Deterministically generate rainfall + water-level gauge locations."""
    rng = random.Random(seed if seed is not None else settings.simulation_seed)
    min_lng, min_lat, max_lng, max_lat = DEMO_DISTRICT_BBOX

    sensors: list[Sensor] = []

    # 12 rainfall gauges spread across the district.
    for i in range(12):
        lat = rng.uniform(min_lat + 0.01, max_lat - 0.01)
        lng = rng.uniform(min_lng + 0.01, max_lng - 0.01)
        sensors.append(Sensor(
            id=f"RG-{i + 1:02d}",
            name=f"Rainfall Gauge {i + 1:02d}",
            sensor_type="rainfall",
            latitude=round(lat, 5),
            longitude=round(lng, 5),
        ))

    # 6 water-level gauges placed along the river path.
    for i, point in enumerate(_RIVER_PATH):
        # small deterministic offset so gauges sit just beside the river line
        offset = 0.004 * (1 if i % 2 == 0 else -1)
        sensors.append(Sensor(
            id=f"WG-{i + 1:02d}",
            name=f"Water-Level Gauge {i + 1:02d}",
            sensor_type="water_level",
            latitude=round(point[1] + offset, 5),
            longitude=round(point[0], 5),
        ))

    return sensors


def generate_water_features() -> list[WaterFeature]:
    """Return the demo river and water bodies."""
    features: list[WaterFeature] = []

    features.append(WaterFeature(
        id="RIVER-GANGA-01",
        name="Ganga (simulated reach)",
        kind="river",
        geometry={"type": "LineString", "coordinates": _RIVER_PATH},
    ))

    for idx, (lat, lng, r) in enumerate(_water_bodies(), start=1):
        ring = [
            [lng - r, lat - r],
            [lng + r, lat - r],
            [lng + r, lat + r],
            [lng - r, lat + r],
            [lng - r, lat - r],
        ]
        features.append(WaterFeature(
            id=f"WB-{idx:02d}",
            name=f"Water Body {idx}",
            kind="water_body",
            geometry={"type": "Polygon", "coordinates": [ring]},
        ))

    return features


# ─── GeoJSON builders ────────────────────────────────────────────────────────

def district_feature() -> dict[str, Any]:
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [DEMO_DISTRICT_POLYGON]},
        "properties": {
            "id": "DEMO-DISTRICT",
            "name": DEMO_DISTRICT_NAME,
            "centre": list(DEMO_DISTRICT_CENTRE),
            "bbox": list(DEMO_DISTRICT_BBOX),
            "simulated": True,
            "note": "Simulated demo district boundary — not an administrative cadastre.",
        },
    }


def sensors_feature_collection() -> dict[str, Any]:
    features = []
    for s in generate_sensors():
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s.longitude, s.latitude]},
            "properties": {
                "id": s.id,
                "name": s.name,
                "sensor_type": s.sensor_type,
                "status": s.status,
                "simulated": s.simulated,
                "trust_score": None,  # populated in Stage 5
            },
        })
    return {"type": "FeatureCollection", "features": features}


def water_feature_collection() -> dict[str, Any]:
    features = []
    for w in generate_water_features():
        features.append({
            "type": "Feature",
            "geometry": w.geometry,
            "properties": {
                "id": w.id,
                "name": w.name,
                "kind": w.kind,
                "simulated": w.simulated,
            },
        })
    return {"type": "FeatureCollection", "features": features}


# ─── Simulated farm centroids (Stage 6) ──────────────────────────────────────

@dataclass
class SimFarm:
    """Lightweight simulated farm record for spatial estimation.

    The GP service needs farm centroids without hitting the database.
    These are deterministically generated from the same seed used for sensors,
    ensuring reproducibility.
    """
    id: str
    latitude: float
    longitude: float
    boundary: list[list[float]]  # closed polygon ring, [lng, lat] pairs


def generate_farms(seed: int | None = None, n_farms: int = 100) -> list[SimFarm]:
    """Deterministically generate simulated farm centroids within the demo district."""
    rng = random.Random(seed if seed is not None else settings.simulation_seed + 1)
    min_lng, min_lat, max_lng, max_lat = DEMO_DISTRICT_BBOX

    farms: list[SimFarm] = []
    for i in range(n_farms):
        lat = rng.uniform(min_lat + 0.005, max_lat - 0.005)
        lng = rng.uniform(min_lng + 0.005, max_lng - 0.005)
        area_ha = rng.uniform(0.5, 5.0)
        boundary = farm_centroid_square(lat, lng, area_ha)
        farms.append(SimFarm(
            id=f"SIM-FARM-{i + 1:03d}",
            latitude=round(lat, 5),
            longitude=round(lng, 5),
            boundary=boundary,
        ))
    return farms
