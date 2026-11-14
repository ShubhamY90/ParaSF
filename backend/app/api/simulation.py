"""Stage 4 simulation endpoints.

REST surface:
  GET  /api/simulation/scenarios          — list available scenario presets
  GET  /api/simulation/runs               — list all simulation runs
  POST /api/simulation/runs               — create a new run (insurer/admin)
  GET  /api/simulation/runs/{id}          — get run metadata
  POST /api/simulation/runs/{id}/control  — start | pause | reset | step
  GET  /api/simulation/runs/{id}/snapshot — full snapshot at current tick
  GET  /api/simulation/runs/{id}/stream   — SSE: tick-by-tick snapshots (auto-advance)

The snapshot endpoint is the primary data source for the frontend map overlays.
The SSE stream pushes compressed snapshot events so the map updates in real time.

Design note: "running" is tracked in the DB. The SSE handler advances the tick
in a loop — it is stateless per request (each tick is computed from scratch).
Only one SSE client needs to be active for the simulation to advance; in a
production system this would be a background task, but for the hackathon the
SSE consumer drives the clock.
"""
import asyncio
import json
import time
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.models.simulation import SimulationRun
from app.models.user import UserRole
from app.core.deps import require_role
from app.core.security import get_current_user
from app.core.config import settings
from app.schemas.simulation import (
    ScenarioInfo, SimulationRunOut, SimulationRunCreate,
    TickControl, SnapshotOut, GaugeReadingOut, StormCellOut,
)
from app.services.simulation import (
    ScenarioPreset, SCENARIO_META, WeatherSimulator,
    rainfall_intensity_geojson, flood_area_geojson, water_levels_geojson,
)

router = APIRouter(prefix="/api/simulation", tags=["simulation"])

# Tick interval in seconds for the SSE auto-advance.
_TICK_INTERVAL_S = 1.5


# ── Scenario catalogue ───────────────────────────────────────────────────────

@router.get("/scenarios", response_model=list[ScenarioInfo])
def list_scenarios():
    """Return all available scenario presets with metadata."""
    return [
        ScenarioInfo(
            preset=preset.value,
            label=meta["label"],
            description=meta["description"],
            total_ticks=meta["total_ticks"],
        )
        for preset, meta in SCENARIO_META.items()
    ]


# ── Run management ────────────────────────────────────────────────────────────

@router.post("/runs", response_model=SimulationRunOut, status_code=201)
def create_run(
    body: SimulationRunCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin)),
):
    """Create a new simulation run. Only insurer / admin can create runs."""
    seed = body.seed if body.seed is not None else settings.simulation_seed
    meta = SCENARIO_META[body.scenario]
    run = SimulationRun(
        scenario=body.scenario.value,
        seed=seed,
        current_tick=0,
        total_ticks=meta["total_ticks"],
        status="paused",
        created_by=current_user.id,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    return run


@router.get("/runs", response_model=list[SimulationRunOut])
def list_runs(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(SimulationRun).order_by(SimulationRun.id.desc()).limit(20).all()


@router.get("/runs/{run_id}", response_model=SimulationRunOut)
def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    run = _run_or_404(db, run_id)
    return run


# ── Simulation controls ───────────────────────────────────────────────────────

@router.post("/runs/{run_id}/control", response_model=SimulationRunOut)
def control_run(
    run_id: int,
    body: TickControl,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin)),
):
    """Control a simulation run: start | pause | reset | step."""
    run = _run_or_404(db, run_id)
    action = body.action.lower()

    if action == "start":
        if run.status != "complete":
            run.status = "running"
    elif action == "pause":
        run.status = "paused"
    elif action == "reset":
        run.current_tick = 0
        run.status = "paused"
    elif action == "step":
        if run.current_tick < run.total_ticks - 1:
            run.current_tick += 1
        if run.current_tick >= run.total_ticks - 1:
            run.status = "complete"
        else:
            run.status = "paused"
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action '{action}'. Use: start | pause | reset | step")

    db.commit()
    db.refresh(run)
    return run


# ── Snapshot ──────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/snapshot", response_model=SnapshotOut)
def get_snapshot(
    run_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return the full simulation state at the run's current tick."""
    run = _run_or_404(db, run_id)
    return _build_snapshot(run)


# ── SSE stream ────────────────────────────────────────────────────────────────

@router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: int,
    request: Request,
    token: str | None = None,
    db: Session = Depends(get_db),
):
    """Server-Sent Events stream.

    Accepts the JWT as either an Authorization: Bearer header or a ``token``
    query parameter (necessary because EventSource doesn't support custom
    headers in browsers).

    While the run is in 'running' status this endpoint advances the tick once
    per ``_TICK_INTERVAL_S`` seconds and pushes the snapshot as a JSON SSE event.
    When paused or complete it sends a 'heartbeat' event every 2 s so the client
    knows the connection is alive.

    The client drives control (start/pause/reset) via the REST control endpoint;
    the SSE stream only reads and advances.
    """
    # Resolve auth: prefer Authorization header, fall back to ?token= query param.
    from app.core.security import get_user_from_token

    auth_header = request.headers.get("authorization", "")
    raw_token = token
    if not raw_token and auth_header.lower().startswith("bearer "):
        raw_token = auth_header[7:]
    if not raw_token:
        from fastapi.responses import Response
        return Response(status_code=401, content="Missing authentication token")
    try:
        current_user = get_user_from_token(raw_token, db)
    except Exception:
        from fastapi.responses import Response
        return Response(status_code=401, content="Invalid token")

    run = _run_or_404(db, run_id)

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            # Reload run from DB on each iteration to pick up control changes.
            db.expire(run)
            db.refresh(run)

            if run.status == "running":
                snap_data = _build_snapshot(run)
                yield f"event: snapshot\ndata: {json.dumps(snap_data.model_dump(mode='json'))}\n\n"

                # Advance tick
                if run.current_tick < run.total_ticks - 1:
                    run.current_tick += 1
                else:
                    run.status = "complete"
                db.commit()

                await asyncio.sleep(_TICK_INTERVAL_S)
            else:
                # Paused or complete — send a lightweight heartbeat.
                heartbeat = {
                    "run_id": run.id,
                    "status": run.status,
                    "tick": run.current_tick,
                    "total_ticks": run.total_ticks,
                }
                yield f"event: heartbeat\ndata: {json.dumps(heartbeat)}\n\n"
                await asyncio.sleep(2.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _run_or_404(db: Session, run_id: int) -> SimulationRun:
    run = db.get(SimulationRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


def _build_snapshot(run: SimulationRun) -> SnapshotOut:
    preset = ScenarioPreset(run.scenario)
    sim = WeatherSimulator(preset, base_seed=run.seed)
    snap = sim.snapshot(run.current_tick)

    gauge_out = [
        GaugeReadingOut(
            sensor_id=r.sensor_id, sensor_type=r.sensor_type,
            lat=r.lat, lng=r.lng, value=r.value, unit=r.unit,
            tick=r.tick, simulated=r.simulated,
            is_faulty=r.is_faulty, fault_type=r.fault_type,
        )
        for r in snap.gauge_readings
    ]
    storm_out = [
        StormCellOut(lat=c.lat, lng=c.lng, peak_mm_hr=c.peak_mm_hr, radius_deg=c.radius_deg)
        for c in snap.storm_cells
    ]

    return SnapshotOut(
        run_id=run.id,
        scenario=run.scenario,
        tick=snap.tick,
        total_ticks=snap.total_ticks,
        simulated_hour=snap.simulated_hour,
        status=run.status,
        gauge_readings=gauge_out,
        storm_cells=storm_out,
        flood_active=snap.flood_active,
        flood_intensity=snap.flood_intensity,
        rainfall_geojson=rainfall_intensity_geojson(snap),
        flood_geojson=flood_area_geojson(snap),
        water_geojson=water_levels_geojson(snap),
    )
