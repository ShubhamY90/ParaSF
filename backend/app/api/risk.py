"""Stage 6 — Farm-level risk assessment endpoints.

POST /api/risk/assess                  — run GP estimation for a tick, persist results
GET  /api/risk/{run_id}                — latest risk layer for a run (all farms)
GET  /api/risk/{run_id}/{farm_id}      — single farm estimate history
GET  /api/risk/geojson/{run_id}        — GeoJSON FeatureCollection coloured by risk category
"""
from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.models.risk import FarmRiskEstimate
from app.models.sensor import SensorTrustScore
from app.models.simulation import SimulationRun
from app.core.security import get_current_user
from app.schemas.risk import FarmRiskEstimateOut, RiskLayerOut, RiskAssessRequest
from app.services.risk import assess_farms, MODEL_VERSION
from app.services.simulation import ScenarioPreset, WeatherSimulator
from app.services.geo import generate_farms

router = APIRouter(prefix="/api/risk", tags=["risk"])

# ─── Risk colour mapping for GeoJSON ─────────────────────────────────────────

_RISK_COLOUR = {
    "low":                   "#22c55e",   # green-500
    "moderate":              "#eab308",   # yellow-500
    "high":                  "#f97316",   # orange-500
    "extreme":               "#ef4444",   # red-500
    "insufficient_evidence": "#64748b",   # slate-500
    "unknown":               "#64748b",
}


# ─── Assess / persist ─────────────────────────────────────────────────────────

@router.post("/assess", response_model=RiskLayerOut)
def run_risk_assessment(
    body: RiskAssessRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Run the GP spatial estimation for all farms at the given tick and persist.

    Idempotent: calling again for the same (run_id, tick) upserts each farm row.
    Requires that fault detection (Stage 5) has been run first to build trust scores.
    Falls back gracefully if no trust scores exist yet (all sensors get trust=0.5).
    """
    run = db.get(SimulationRun, body.run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    tick = body.tick if body.tick is not None else run.current_tick
    tick = max(0, min(tick, run.total_ticks - 1))

    # Load all trust scores for this run (we use the latest per sensor).
    trust_rows = (
        db.query(SensorTrustScore)
        .filter(SensorTrustScore.run_id == run.id)
        .all()
    )

    sim = WeatherSimulator(ScenarioPreset(run.scenario), base_seed=run.seed)
    farm_results = assess_farms(run.id, tick, trust_rows, sim)

    # Persist / upsert each farm estimate.
    for fr in farm_results:
        existing = (
            db.query(FarmRiskEstimate)
            .filter(
                FarmRiskEstimate.run_id == run.id,
                FarmRiskEstimate.farm_id == fr.farm_id,
                FarmRiskEstimate.tick == tick,
            )
            .first()
        )
        sensor_json = json.dumps(fr.supporting_sensors)
        if existing:
            existing.estimated_rainfall_mm = fr.estimated_rainfall_mm
            existing.uncertainty_mm        = fr.uncertainty_mm
            existing.lower_ci              = fr.lower_ci
            existing.upper_ci              = fr.upper_ci
            existing.risk_category         = fr.risk_category
            existing.flood_risk_score      = fr.flood_risk_score
            existing.supporting_sensors    = sensor_json
            existing.evidence_note         = fr.evidence_note
            existing.model_version         = fr.model_version
        else:
            db.add(FarmRiskEstimate(
                run_id=run.id,
                farm_id=fr.farm_id,
                tick=tick,
                estimated_rainfall_mm=fr.estimated_rainfall_mm,
                uncertainty_mm=fr.uncertainty_mm,
                lower_ci=fr.lower_ci,
                upper_ci=fr.upper_ci,
                risk_category=fr.risk_category,
                flood_risk_score=fr.flood_risk_score,
                supporting_sensors=sensor_json,
                evidence_note=fr.evidence_note,
                model_version=fr.model_version,
            ))
    db.commit()

    return _build_layer(run.id, tick, farm_results)


# ─── Risk GeoJSON ─────────────────────────────────────────────────────────────

@router.get("/geojson/{run_id}")
def risk_geojson(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """GeoJSON FeatureCollection of farm polygons coloured by risk category.

    Falls back to grey / insufficient_evidence for farms not yet assessed.
    """
    run = db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    # Latest tick with data.
    rows = (
        db.query(FarmRiskEstimate)
        .filter(FarmRiskEstimate.run_id == run_id)
        .order_by(FarmRiskEstimate.tick.desc())
        .all()
    )
    latest: dict[str, FarmRiskEstimate] = {}
    for r in rows:
        if r.farm_id not in latest:
            latest[r.farm_id] = r

    farms = generate_farms()
    features = []
    for farm in farms:
        est = latest.get(farm.id)
        risk_cat = est.risk_category if est else "insufficient_evidence"
        colour = _RISK_COLOUR.get(risk_cat, "#64748b")

        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [farm.boundary],
            },
            "properties": {
                "farm_id": farm.id,
                "farmer_name": "Registered farmer",  # privacy label
                "risk_category": risk_cat,
                "colour": colour,
                "estimated_rainfall_mm": est.estimated_rainfall_mm if est else None,
                "uncertainty_mm": est.uncertainty_mm if est else None,
                "lower_ci": est.lower_ci if est else None,
                "upper_ci": est.upper_ci if est else None,
                "flood_risk_score": est.flood_risk_score if est else None,
                "simulated": True,
                "note": (
                    "Simulated estimate — not a confirmed physical flood boundary"
                ),
            },
        })

    return {"type": "FeatureCollection", "features": features}


# ─── Latest risk layer for a run ─────────────────────────────────────────────

@router.get("/{run_id}", response_model=RiskLayerOut)
def get_risk_layer(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the most recently persisted risk layer (latest tick with data)."""
    run = db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")

    rows = (
        db.query(FarmRiskEstimate)
        .filter(FarmRiskEstimate.run_id == run_id)
        .order_by(FarmRiskEstimate.tick.desc())
        .all()
    )
    if not rows:
        raise HTTPException(
            status_code=404,
            detail="No risk estimates found — run POST /api/risk/assess first",
        )

    latest_tick = rows[0].tick
    latest = [r for r in rows if r.tick == latest_tick]
    return _build_layer_from_db(run_id, latest_tick, latest)


# ─── Single farm estimate history ─────────────────────────────────────────────

@router.get("/{run_id}/{farm_id}", response_model=list[FarmRiskEstimateOut])
def get_farm_risk_history(
    run_id: int,
    farm_id: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return per-tick risk history for a single farm."""
    rows = (
        db.query(FarmRiskEstimate)
        .filter(
            FarmRiskEstimate.run_id == run_id,
            FarmRiskEstimate.farm_id == farm_id,
        )
        .order_by(FarmRiskEstimate.tick)
        .all()
    )
    return [_row_to_out(r) for r in rows]


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _row_to_out(r: FarmRiskEstimate) -> FarmRiskEstimateOut:
    sensors = json.loads(r.supporting_sensors) if r.supporting_sensors else []
    return FarmRiskEstimateOut(
        farm_id=r.farm_id,
        tick=r.tick,
        run_id=r.run_id,
        estimated_rainfall_mm=r.estimated_rainfall_mm,
        uncertainty_mm=r.uncertainty_mm,
        lower_ci=r.lower_ci,
        upper_ci=r.upper_ci,
        risk_category=r.risk_category,
        flood_risk_score=r.flood_risk_score,
        supporting_sensors=sensors,
        evidence_note=r.evidence_note or "",
        model_version=r.model_version or MODEL_VERSION,
    )


def _build_layer(run_id: int, tick: int, farm_results) -> RiskLayerOut:
    out_farms = [
        FarmRiskEstimateOut(
            farm_id=fr.farm_id,
            tick=fr.tick,
            run_id=fr.run_id,
            estimated_rainfall_mm=fr.estimated_rainfall_mm,
            uncertainty_mm=fr.uncertainty_mm,
            lower_ci=fr.lower_ci,
            upper_ci=fr.upper_ci,
            risk_category=fr.risk_category,
            flood_risk_score=fr.flood_risk_score,
            supporting_sensors=fr.supporting_sensors,
            evidence_note=fr.evidence_note,
            model_version=fr.model_version,
        )
        for fr in farm_results
    ]
    return RiskLayerOut(
        run_id=run_id,
        tick=tick,
        farms=out_farms,
        summary=_summarise(out_farms),
    )


def _build_layer_from_db(run_id: int, tick: int, rows: list[FarmRiskEstimate]) -> RiskLayerOut:
    out_farms = [_row_to_out(r) for r in rows]
    return RiskLayerOut(
        run_id=run_id,
        tick=tick,
        farms=out_farms,
        summary=_summarise(out_farms),
    )


def _summarise(farms: list[FarmRiskEstimateOut]) -> dict:
    cats = [f.risk_category for f in farms]
    return {
        "total_farms": len(farms),
        "low":                    cats.count("low"),
        "moderate":               cats.count("moderate"),
        "high":                   cats.count("high"),
        "extreme":                cats.count("extreme"),
        "insufficient_evidence":  cats.count("insufficient_evidence"),
    }

