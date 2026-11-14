"""Stage 6 — Farm-Level Risk Assessment DB model."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from app.db.engine import Base


class FarmRiskEstimate(Base):
    """Persisted risk estimate for one farm at one simulation tick."""

    __tablename__ = "farm_risk_estimates"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False, index=True)
    farm_id = Column(String, nullable=False, index=True)
    tick = Column(Integer, nullable=False)

    # Spatial estimate outputs
    estimated_rainfall_mm = Column(Float, nullable=True)   # trust-weighted GP estimate
    uncertainty_mm = Column(Float, nullable=True)          # posterior std dev (mm/hr)
    lower_ci = Column(Float, nullable=True)                # 10th percentile
    upper_ci = Column(Float, nullable=True)                # 90th percentile

    # Risk classification
    risk_category = Column(String, nullable=False, default="unknown")
    # low | moderate | high | extreme | insufficient_evidence

    # Flood risk (derived from water-level gauges + rainfall estimate)
    flood_risk_score = Column(Float, nullable=True)        # 0.0–1.0

    # Evidence metadata
    supporting_sensors = Column(Text, nullable=True)       # JSON list of sensor IDs
    evidence_note = Column(Text, nullable=True)
    model_version = Column(String, nullable=False, default="gp-v1")
    evidence_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

