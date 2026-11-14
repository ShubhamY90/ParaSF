"""Stage 6 — Pydantic schemas for farm-level risk assessment."""
from __future__ import annotations

from pydantic import BaseModel, Field


class FarmRiskEstimateOut(BaseModel):
    farm_id: str
    tick: int
    run_id: int

    estimated_rainfall_mm: float | None
    uncertainty_mm: float | None
    lower_ci: float | None
    upper_ci: float | None

    risk_category: str
    flood_risk_score: float | None

    supporting_sensors: list[str]
    evidence_note: str
    model_version: str

    simulated: bool = True

    model_config = {"from_attributes": True}


class RiskLayerOut(BaseModel):
    """Full risk layer for a simulation tick — all farms."""
    run_id: int
    tick: int
    farms: list[FarmRiskEstimateOut]
    summary: dict
    simulated: bool = True


class RiskAssessRequest(BaseModel):
    run_id: int
    tick: int | None = Field(None, description="Defaults to the run's current tick")

