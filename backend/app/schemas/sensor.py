"""Pydantic schemas for Stage 5 sensor fault detection endpoints."""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class SensorClassificationOut(BaseModel):
    sensor_id: str
    sensor_type: str
    predicted_class: str
    confidence: float
    trust_score: float
    class_probabilities: Dict[str, float]
    is_flagged: bool
    investigation_note: str
    simulated: bool = True


class SensorTrustScoreOut(BaseModel):
    id: int
    run_id: int
    sensor_id: str
    sensor_type: str
    tick: int
    raw_value: float
    unit: str
    predicted_class: str
    confidence: float
    trust_score: float
    is_flagged: bool
    investigation_note: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassifyRequest(BaseModel):
    run_id: int
    tick: Optional[int] = None   # defaults to run's current_tick


class TrustScoreMapOut(BaseModel):
    """Map of sensor_id → trust_score for quick consumption by the map layer."""
    run_id: int
    tick: int
    scores: Dict[str, float]           # sensor_id → trust_score
    flagged: List[str]                 # sensor_ids with is_flagged=True
    classifications: List[SensorClassificationOut]
    simulated: bool = True


class ModelEvaluationOut(BaseModel):
    classes: List[str]
    classification_report: str
    confusion_matrix: List[List[int]]
    label_order: List[str]
    note: str
