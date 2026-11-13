"""Pydantic schemas for Stage 3 geographic / map-detail endpoints."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class CropBrief(BaseModel):
    crop_type: str
    season: Optional[str] = None
    area_hectares: Optional[float] = None


class PolicyBrief(BaseModel):
    id: int
    policy_number: str
    status: str
    sum_insured: float
    coverage_start: str
    coverage_end: str


class FarmMapDetail(BaseModel):
    """Rich farm record shown in the map detail panel."""
    farm_id: int
    name: str
    area_hectares: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    farmer_label: str
    district: Optional[str] = None
    state: Optional[str] = None
    crops: List[CropBrief] = []
    primary_crop: Optional[str] = None
    policy: Optional[PolicyBrief] = None
    policy_status: str = "none"
    sum_insured: Optional[float] = None

    # Placeholders for later stages — kept explicit so the UI can show a clear
    # "not yet available" message rather than a silent null.
    estimated_rainfall_mm: Optional[float] = None
    risk_category: Optional[str] = None
    claim_status: Optional[str] = None
    stage_notes: List[str] = []

    # Flag so the UI can label simulated vs. real layers.
    in_demo_district: bool = True
