"""Pydantic schemas for Stage 4 simulation endpoints."""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel
from app.services.simulation import ScenarioPreset, SCENARIO_META


class ScenarioInfo(BaseModel):
    preset: str
    label: str
    description: str
    total_ticks: int


class SimulationRunOut(BaseModel):
    id: int
    scenario: str
    seed: int
    current_tick: int
    total_ticks: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class SimulationRunCreate(BaseModel):
    scenario: ScenarioPreset
    seed: Optional[int] = None   # defaults to settings.simulation_seed


class TickControl(BaseModel):
    action: str   # "start" | "pause" | "reset" | "step"


class GaugeReadingOut(BaseModel):
    sensor_id: str
    sensor_type: str
    lat: float
    lng: float
    value: float
    unit: str
    tick: int
    simulated: bool
    is_faulty: bool
    fault_type: Optional[str]


class StormCellOut(BaseModel):
    lat: float
    lng: float
    peak_mm_hr: float
    radius_deg: float


class SnapshotOut(BaseModel):
    run_id: int
    scenario: str
    tick: int
    total_ticks: int
    simulated_hour: int
    status: str
    gauge_readings: List[GaugeReadingOut]
    storm_cells: List[StormCellOut]
    flood_active: bool
    flood_intensity: float
    rainfall_geojson: Any          # FeatureCollection
    flood_geojson: Optional[Any]   # Feature | null
    water_geojson: Any             # FeatureCollection
    simulated: bool = True
