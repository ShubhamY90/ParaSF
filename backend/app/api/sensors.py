"""Stage 5 — Sensor fault detection & trust score endpoints.

GET  /api/sensors/model/evaluation    — per-class precision/recall/F1 + confusion matrix
POST /api/sensors/classify            — classify all gauges at a given run+tick
GET  /api/sensors/trust/{run_id}      — latest persisted trust scores for a run
GET  /api/sensors/trust/{run_id}/{sensor_id} — single sensor trust score history
GET  /api/sensors/geojson/{run_id}    — sensor FeatureCollection annotated with trust scores
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.models.sensor import SensorTrustScore
from app.models.simulation import SimulationRun
from app.models.user import UserRole
from app.core.deps import require_role
from app.core.security import get_current_user
from app.schemas.sensor import (
    SensorClassificationOut, SensorTrustScoreOut,
    ClassifyRequest, TrustScoreMapOut, ModelEvaluationOut,
)
from app.services.fault_detection import (
    classify_readings, get_model_evaluation, FAULT_CLASSES,
)
from app.services.simulation import ScenarioPreset, WeatherSimulator
from app.services.geo import generate_sensors

router = APIRouter(prefix="/api/sensors", tags=["sensors"])


# ── Model evaluation ──────────────────────────────────────────────────────────

@router.get("/model/evaluation", response_model=ModelEvaluationOut)
def model_evaluation(current_user=Depends(get_current_user)):
    """Return per-class evaluation metrics for the fault detection model."""
    return get_model_evaluation()


# ── Classify sensors at a tick ────────────────────────────────────────────────

@router.post("/classify", response_model=TrustScoreMapOut)
def classify_sensors(
    body: ClassifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Run fault classification on all rainfall gauges at the specified tick
    and persist the results.  Returns the full trust-score map.

    Idempotent: calling again for the same (run_id, tick) overwrites the
    previous result for each sensor at that tick.
    """
    run = db.get(SimulationRun, body.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    tick = body.tick if body.tick is not None else run.current_tick
    tick = max(0, min(tick, run.total_ticks - 1))

    # Build snapshot for this tick.
    sim = WeatherSimulator(ScenarioPreset(run.scenario), base_seed=run.seed)
    snap = sim.snapshot(tick)

    # Build a simple history map from ticks [max(0,tick-4)..tick-1].
    history_map: dict[str, list[float]] = {}
    for t in range(max(0, tick - 4), tick):
        past = sim.snapshot(t)
        for r in past.gauge_readings:
            if r.sensor_type == "rainfall":
                history_map.setdefault(r.sensor_id, []).append(r.value)

    classifications = classify_readings(snap.gauge_readings, history_map)

    # Persist / upsert each classification.
    for cls in classifications:
        # Find the raw reading.
        raw_r = next((r for r in snap.gauge_readings if r.sensor_id == cls.sensor_id), None)
        raw_val = raw_r.value if raw_r else 0.0
        unit    = raw_r.unit  if raw_r else "mm/hr"

        existing = (
            db.query(SensorTrustScore)
            .filter(
                SensorTrustScore.run_id == run.id,
                SensorTrustScore.sensor_id == cls.sensor_id,
                SensorTrustScore.tick == tick,
            )
            .first()
        )
        if existing:
            existing.predicted_class    = cls.predicted_class
            existing.confidence         = cls.confidence
            existing.trust_score        = cls.trust_score
            existing.is_flagged         = cls.is_flagged
            existing.investigation_note = cls.investigation_note
        else:
            db.add(SensorTrustScore(
                run_id=run.id,
                sensor_id=cls.sensor_id,
                sensor_type=cls.sensor_type,
                tick=tick,
                raw_value=raw_val,
                unit=unit,
                predicted_class=cls.predicted_class,
                confidence=cls.confidence,
                trust_score=cls.trust_score,
                is_flagged=cls.is_flagged,
                investigation_note=cls.investigation_note,
            ))
    db.commit()

    return _build_trust_map(run.id, tick, classifications)


# ── Latest trust scores for a run ─────────────────────────────────────────────

@router.get("/trust/{run_id}", response_model=TrustScoreMapOut)
def get_trust_scores(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the most recently persisted trust scores for each sensor in this run."""
    run = db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    # Get the latest tick that has data.
    rows = (
        db.query(SensorTrustScore)
        .filter(SensorTrustScore.run_id == run_id)
        .order_by(SensorTrustScore.tick.desc())
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="No trust scores found — run /classify first")

    latest_tick = rows[0].tick
    latest_rows = [r for r in rows if r.tick == latest_tick]

    classifications = [
        SensorClassificationOut(
            sensor_id=r.sensor_id,
            sensor_type=r.sensor_type,
            predicted_class=r.predicted_class,
            confidence=r.confidence,
            trust_score=r.trust_score,
            class_probabilities={},  # not stored; would need JSON column for full proba
            is_flagged=r.is_flagged,
            investigation_note=r.investigation_note,
        )
        for r in latest_rows
    ]
    return _build_trust_map(run_id, latest_tick, classifications)


# ── Single sensor trust score history ─────────────────────────────────────────

@router.get("/trust/{run_id}/{sensor_id}", response_model=list[SensorTrustScoreOut])
def get_sensor_history(
    run_id: int,
    sensor_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the trust score history for a single sensor across all classified ticks."""
    rows = (
        db.query(SensorTrustScore)
        .filter(
            SensorTrustScore.run_id == run_id,
            SensorTrustScore.sensor_id == sensor_id,
        )
        .order_by(SensorTrustScore.tick)
        .all()
    )
    return rows


# ── Sensor GeoJSON annotated with trust scores ─────────────────────────────────

@router.get("/geojson/{run_id}")
def sensor_trust_geojson(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return a GeoJSON FeatureCollection of all sensors annotated with the
    latest trust score and fault classification for the given run.

    Falls back to trust_score=1.0, predicted_class='normal' for sensors
    that have not yet been classified.
    """
    run = db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    # Build lookup: sensor_id → latest trust row.
    rows = (
        db.query(SensorTrustScore)
        .filter(SensorTrustScore.run_id == run_id)
        .order_by(SensorTrustScore.tick.desc())
        .all()
    )
    latest: dict[str, SensorTrustScore] = {}
    for r in rows:
        if r.sensor_id not in latest:
            latest[r.sensor_id] = r

    sensors = generate_sensors()
    features = []
    for s in sensors:
        ts = latest.get(s.id)
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [s.longitude, s.latitude]},
            "properties": {
                "id": s.id,
                "name": s.name,
                "sensor_type": s.sensor_type,
                "trust_score": ts.trust_score if ts else 1.0,
                "predicted_class": ts.predicted_class if ts else "normal",
                "is_flagged": ts.is_flagged if ts else False,
                "confidence": ts.confidence if ts else None,
                "investigation_note": ts.investigation_note if ts else "Not yet classified.",
                "simulated": True,
            },
        })
    return {"type": "FeatureCollection", "features": features}


# ── Helper ─────────────────────────────────────────────────────────────────────

def _build_trust_map(run_id: int, tick: int, classifications: list) -> TrustScoreMapOut:
    """Accept either SensorClassificationOut or SensorClassification dataclass."""
    out_list: list[SensorClassificationOut] = []
    for c in classifications:
        if isinstance(c, SensorClassificationOut):
            out_list.append(c)
        else:
            out_list.append(SensorClassificationOut(
                sensor_id=c.sensor_id,
                sensor_type=c.sensor_type,
                predicted_class=c.predicted_class,
                confidence=c.confidence,
                trust_score=c.trust_score,
                class_probabilities=c.class_probabilities,
                is_flagged=c.is_flagged,
                investigation_note=c.investigation_note,
            ))
    scores  = {c.sensor_id: c.trust_score for c in out_list}
    flagged = [c.sensor_id for c in out_list if c.is_flagged]
    return TrustScoreMapOut(
        run_id=run_id, tick=tick,
        scores=scores, flagged=flagged,
        classifications=out_list,
    )
