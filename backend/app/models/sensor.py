"""Stage 5 ORM model: SensorTrustScore — persists per-sensor classification results."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.engine import Base


class SensorTrustScore(Base):
    """Persisted trust-score record for one sensor at one simulation tick.

    The original reading is always preserved (stored in ``raw_value``).
    The classification result is advisory — it must not automatically override
    the reading in downstream calculations.
    """
    __tablename__ = "sensor_trust_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(Integer, ForeignKey("simulation_runs.id"), nullable=False, index=True)
    sensor_id: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    sensor_type: Mapped[str] = mapped_column(String(20), nullable=False)
    tick: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(10), nullable=False)
    predicted_class: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    trust_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    investigation_note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
