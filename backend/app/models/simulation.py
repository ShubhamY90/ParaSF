"""Stage 4 ORM models: SimulationRun stores scenario state for replay."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.engine import Base


class SimulationRun(Base):
    """A simulation session: scenario preset + current tick.

    Storing the run in the DB means the same (scenario, seed) can always be
    replayed and the client can reconnect and resume.
    """
    __tablename__ = "simulation_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scenario: Mapped[str] = mapped_column(String(50), nullable=False)
    seed: Mapped[int] = mapped_column(Integer, nullable=False)
    current_tick: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_ticks: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="paused", nullable=False)
    # "paused" | "running" | "complete" | "reset"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow,
                                                   onupdate=datetime.utcnow)
    created_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
