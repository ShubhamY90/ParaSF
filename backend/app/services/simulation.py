"""Stage 4 — Weather & Flood Simulation engine.

Pure-Python, no ML dependencies. Deterministic from a fixed seed so the same
scenario is always reproducible. Builds on the Stage-3 geo service (sensor
locations, district geometry).

Design
------
*Simulation time* advances in configurable ticks. Each tick represents one
hour of simulated time. The engine is stateless — given (scenario_id, tick)
it always produces the same output. Callers request snapshots at any tick;
they do not need to replay from tick 0.

Scenarios
---------
Five presets (each has a fixed scenario seed so they are independent of each
other but always reproducible):

  NORMAL       — typical background rainfall, no flood event.
  BROAD_RAIN   — widespread moderate rainfall across the district.
  SEVERE_FLOOD — intense rain + rising river + expanding flood polygon.
  LOCALISED    — single intense storm cell over a small area.
  FAULTY_SENSOR — broad rain with one gauge injecting a spike fault (Stage 5
                  trust-score input).

Output at each tick
-------------------
- Per-gauge reading: mm/hr rainfall or cm water level.
- Moving storm-cell centre (lat, lng).
- Rainfall-intensity GeoJSON FeatureCollection (colour/opacity driven by mm/hr).
- Flood-affected-area GeoJSON Feature (Polygon, clearly labelled simulated).
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from app.services.geo import (
    DEMO_DISTRICT_BBOX,
    DEMO_DISTRICT_CENTRE,
    generate_sensors,
    Sensor,
)
from app.core.config import settings


# ─── Scenario definitions ────────────────────────────────────────────────────

class ScenarioPreset(str, Enum):
    NORMAL        = "normal"
    BROAD_RAIN    = "broad_rain"
    SEVERE_FLOOD  = "severe_flood"
    LOCALISED     = "localised"
    FAULTY_SENSOR = "faulty_sensor"


SCENARIO_META: dict[ScenarioPreset, dict[str, Any]] = {
    ScenarioPreset.NORMAL: {
        "label": "Normal Weather",
        "description": "Background light rainfall, no significant events.",
        "seed_offset": 0,
        "total_ticks": 48,
    },
    ScenarioPreset.BROAD_RAIN: {
        "label": "Broad Rainfall Event",
        "description": "Widespread moderate rain moving across the district over 24 hours.",
        "seed_offset": 100,
        "total_ticks": 48,
    },
    ScenarioPreset.SEVERE_FLOOD: {
        "label": "Severe Flood Event",
        "description": "Intense rainfall triggers river flooding; flood polygon expands over time.",
        "seed_offset": 200,
        "total_ticks": 72,
    },
    ScenarioPreset.LOCALISED: {
        "label": "Localised Rainfall",
        "description": "Single intense storm cell over a small area; most gauges read normal.",
        "seed_offset": 300,
        "total_ticks": 36,
    },
    ScenarioPreset.FAULTY_SENSOR: {
        "label": "Faulty Sensor Event",
        "description": "Broad rain with one gauge injecting a sudden spike (Stage 5 input).",
        "seed_offset": 400,
        "total_ticks": 48,
    },
}


# ─── Data classes ────────────────────────────────────────────────────────────

@dataclass
class StormCell:
    """A moving Gaussian rainfall source."""
    lat: float
    lng: float
    peak_mm_hr: float    # rainfall at the cell centre
    radius_deg: float    # 1-sigma radius in degrees (approx)


@dataclass
class GaugeReading:
    sensor_id: str
    sensor_type: str     # "rainfall" | "water_level"
    lat: float
    lng: float
    value: float         # mm/hr (rainfall) or cm (water level)
    unit: str
    tick: int
    simulated: bool = True
    is_faulty: bool = False
    fault_type: str | None = None


@dataclass
class SimulationSnapshot:
    scenario: ScenarioPreset
    tick: int
    total_ticks: int
    simulated_hour: int           # 0-based hour in the scenario
    gauge_readings: list[GaugeReading]
    storm_cells: list[StormCell]
    flood_active: bool
    flood_intensity: float        # 0.0 – 1.0
    simulated: bool = True


# ─── Simulation engine ───────────────────────────────────────────────────────

class WeatherSimulator:
    """Deterministic weather simulation engine.

    Instantiate once per request (stateless — no mutable runtime state).
    ``snapshot(tick)`` always returns the same result for the same inputs.
    """

    def __init__(self, preset: ScenarioPreset, base_seed: int | None = None):
        self.preset = preset
        meta = SCENARIO_META[preset]
        self.total_ticks: int = meta["total_ticks"]
        seed = (base_seed if base_seed is not None else settings.simulation_seed) + meta["seed_offset"]
        self._rng = random.Random(seed)
        self._sensors: list[Sensor] = generate_sensors(seed)
        self._storm_path = self._gen_storm_path()
        self._faulty_gauge_idx: int | None = self._pick_faulty_gauge()

    # ── Storm path ────────────────────────────────────────────────────────────

    def _gen_storm_path(self) -> list[tuple[float, float]]:
        """Generate a list of (lat, lng) waypoints for the storm cell to follow."""
        min_lng, min_lat, max_lng, max_lat = DEMO_DISTRICT_BBOX
        rng = self._rng
        # Start near one edge of the district and move across.
        start_lat = rng.uniform(min_lat + 0.05, max_lat - 0.05)
        start_lng = min_lng + 0.02
        end_lat   = rng.uniform(min_lat + 0.05, max_lat - 0.05)
        end_lng   = max_lng - 0.02
        n_waypoints = 8
        path: list[tuple[float, float]] = []
        for i in range(n_waypoints):
            t = i / (n_waypoints - 1)
            lat = start_lat + (end_lat - start_lat) * t + rng.gauss(0, 0.015)
            lng = start_lng + (end_lng - start_lng) * t
            path.append((round(lat, 5), round(lng, 5)))
        return path

    def _pick_faulty_gauge(self) -> int | None:
        if self.preset == ScenarioPreset.FAULTY_SENSOR:
            # Pick one rainfall gauge to inject a spike into.
            rain_gauges = [i for i, s in enumerate(self._sensors) if s.sensor_type == "rainfall"]
            return self._rng.choice(rain_gauges)
        return None

    # ── Storm cell at tick t ──────────────────────────────────────────────────

    def _storm_cell_at(self, tick: int) -> StormCell | None:
        preset = self.preset
        t = tick / max(self.total_ticks - 1, 1)
        path = self._storm_path
        # Interpolate position along the path.
        idx = t * (len(path) - 1)
        lo = int(idx)
        hi = min(lo + 1, len(path) - 1)
        frac = idx - lo
        lat = path[lo][0] + (path[hi][0] - path[lo][0]) * frac
        lng = path[lo][1] + (path[hi][1] - path[lo][1]) * frac

        if preset == ScenarioPreset.NORMAL:
            return None  # no active storm cell in normal weather
        if preset == ScenarioPreset.BROAD_RAIN:
            # Wide, moderate storm
            peak = 15.0 + 10.0 * math.sin(math.pi * t)
            return StormCell(lat=lat, lng=lng, peak_mm_hr=peak, radius_deg=0.15)
        if preset == ScenarioPreset.SEVERE_FLOOD:
            # Intense storm, peaks at mid-scenario
            peak = 60.0 * math.sin(math.pi * t) + 10.0
            return StormCell(lat=lat, lng=lng, peak_mm_hr=peak, radius_deg=0.10)
        if preset == ScenarioPreset.LOCALISED:
            # Narrow, intense cell
            peak = 80.0 * math.sin(math.pi * t)
            return StormCell(lat=lat, lng=lng, peak_mm_hr=peak, radius_deg=0.04)
        if preset == ScenarioPreset.FAULTY_SENSOR:
            peak = 20.0 + 10.0 * math.sin(math.pi * t)
            return StormCell(lat=lat, lng=lng, peak_mm_hr=peak, radius_deg=0.14)
        return None

    # ── Gauge reading at tick t ───────────────────────────────────────────────

    def _gaussian_mm(self, sensor: Sensor, cell: StormCell | None, tick: int) -> float:
        """Background + storm contribution for a rainfall gauge.

        When ERA5 data is available the background is replaced by the real
        area-mean signal for that tick, scaled by a small per-sensor jitter so
        individual gauges differ slightly (spatially realistic). The storm-cell
        Gaussian is then added on top, ensuring the simulation scenarios still
        produce distinct patterns even when grounded in real data.
        """
        from app.services.era5_loader import get_base_signal, era5_available  # local to avoid circular

        rng = random.Random(hash((sensor.id, tick, self.preset)) & 0xFFFFFFFF)

        if era5_available() and self.preset in (ScenarioPreset.SEVERE_FLOOD, ScenarioPreset.BROAD_RAIN, ScenarioPreset.FAULTY_SENSOR):
            era5_base = get_base_signal(tick)
            # Per-sensor spatial jitter: ±20 % drawn deterministically from sensor+tick hash
            jitter = rng.uniform(0.80, 1.20)
            background = max(0.0, era5_base * jitter)
        else:
            background = rng.uniform(0.1, 1.5)

        if cell is None:
            return background
        d_lat = sensor.latitude  - cell.lat
        d_lng = sensor.longitude - cell.lng
        dist  = math.sqrt(d_lat**2 + d_lng**2)
        contrib = cell.peak_mm_hr * math.exp(-0.5 * (dist / cell.radius_deg) ** 2)
        return background + contrib

    def _water_level_cm(self, sensor: Sensor, tick: int, flood_intensity: float) -> float:
        """Simulated water-level reading in cm above baseline."""
        rng = random.Random(hash((sensor.id, tick, self.preset)) & 0xFFFFFFFF)
        baseline = rng.uniform(80.0, 120.0)
        flood_rise = flood_intensity * 180.0  # up to +180 cm during peak flood
        noise = rng.gauss(0, 2.0)
        return round(baseline + flood_rise + noise, 1)

    # ── Flood polygon at tick t ───────────────────────────────────────────────

    def _flood_state(self, tick: int) -> tuple[bool, float]:
        """Return (flood_active, intensity 0–1)."""
        t = tick / max(self.total_ticks - 1, 1)
        if self.preset == ScenarioPreset.SEVERE_FLOOD:
            # Flood builds from tick 20%, peaks at 60%, recedes by 90%.
            if t < 0.20:
                return False, 0.0
            elif t < 0.60:
                intensity = (t - 0.20) / 0.40
                return True, round(intensity, 3)
            elif t < 0.90:
                intensity = 1.0 - (t - 0.60) / 0.30
                return True, round(intensity, 3)
            else:
                return False, 0.0
        return False, 0.0

    def _flood_polygon(self, intensity: float) -> list[list[float]]:
        """Return a [lng, lat] ring for the simulated flood-affected area.

        The polygon expands from the river corridor outward as intensity rises.
        Clearly labelled as simulated in the properties.
        """
        # Base flood corridor along the Ganga reach.
        from app.services.geo import _RIVER_PATH
        # Build a buffer of width proportional to intensity.
        half_w = 0.012 + intensity * 0.040  # 0.012° to 0.052° (~1.3–5.8 km)
        # Simple rectangular buffer across first to last river node.
        path = _RIVER_PATH
        ring: list[list[float]] = []
        for point in path:
            ring.append([point[0], point[1] + half_w])
        for point in reversed(path):
            ring.append([point[0], point[1] - half_w])
        ring.append(ring[0])  # close
        return ring

    # ── Main snapshot method ──────────────────────────────────────────────────

    def snapshot(self, tick: int) -> SimulationSnapshot:
        """Return the full simulation state at the given tick.

        Tick is clamped to [0, total_ticks - 1].
        """
        tick = max(0, min(tick, self.total_ticks - 1))
        cell = self._storm_cell_at(tick)
        flood_active, flood_intensity = self._flood_state(tick)

        readings: list[GaugeReading] = []
        for idx, sensor in enumerate(self._sensors):
            if sensor.sensor_type == "rainfall":
                val = self._gaussian_mm(sensor, cell, tick)
                # Inject spike for the faulty gauge
                is_faulty = False
                fault_type: str | None = None
                if self._faulty_gauge_idx is not None and idx == self._faulty_gauge_idx:
                    t_norm = tick / max(self.total_ticks - 1, 1)
                    if 0.3 <= t_norm <= 0.5:
                        val = val + 180.0  # sudden spike
                        is_faulty = True
                        fault_type = "spike"
                readings.append(GaugeReading(
                    sensor_id=sensor.id, sensor_type="rainfall",
                    lat=sensor.latitude, lng=sensor.longitude,
                    value=round(val, 2), unit="mm/hr", tick=tick,
                    is_faulty=is_faulty, fault_type=fault_type,
                ))
            else:
                val = self._water_level_cm(sensor, tick, flood_intensity)
                readings.append(GaugeReading(
                    sensor_id=sensor.id, sensor_type="water_level",
                    lat=sensor.latitude, lng=sensor.longitude,
                    value=val, unit="cm", tick=tick,
                ))

        storm_cells = [cell] if cell else []
        return SimulationSnapshot(
            scenario=self.preset,
            tick=tick,
            total_ticks=self.total_ticks,
            simulated_hour=tick,
            gauge_readings=readings,
            storm_cells=storm_cells,
            flood_active=flood_active,
            flood_intensity=flood_intensity,
        )


# ─── GeoJSON builders (called by API layer) ──────────────────────────────────

def rainfall_intensity_geojson(snap: SimulationSnapshot) -> dict[str, Any]:
    """FeatureCollection of point features with rainfall mm/hr as a property.

    Intensity is 0–100+ mm/hr. Clients colour-map this for the overlay.
    Explicitly labelled as simulated.
    """
    features = []
    for r in snap.gauge_readings:
        if r.sensor_type != "rainfall":
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r.lng, r.lat]},
            "properties": {
                "sensor_id": r.sensor_id,
                "rainfall_mm_hr": r.value,
                "tick": r.tick,
                "is_faulty": r.is_faulty,
                "fault_type": r.fault_type,
                "simulated": True,
            },
        })
    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {"simulated": True, "note": "Simulated rainfall intensity — not observed meteorological data."},
    }


def flood_area_geojson(snap: SimulationSnapshot) -> dict[str, Any] | None:
    """Return a GeoJSON Feature for the flood-affected area, or None if no flood."""
    if not snap.flood_active or snap.flood_intensity < 0.01:
        return None
    sim = WeatherSimulator(snap.scenario)
    ring = sim._flood_polygon(snap.flood_intensity)
    return {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [ring]},
        "properties": {
            "intensity": snap.flood_intensity,
            "tick": snap.tick,
            "simulated": True,
            "note": "Simulated flood-affected area — not a verified flood boundary.",
        },
    }


def water_levels_geojson(snap: SimulationSnapshot) -> dict[str, Any]:
    """FeatureCollection of water-level gauge readings."""
    features = []
    for r in snap.gauge_readings:
        if r.sensor_type != "water_level":
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [r.lng, r.lat]},
            "properties": {
                "sensor_id": r.sensor_id,
                "level_cm": r.value,
                "tick": r.tick,
                "simulated": True,
            },
        })
    return {"type": "FeatureCollection", "features": features}
