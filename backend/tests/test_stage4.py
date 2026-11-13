"""Stage 4 acceptance tests: Weather & Flood Simulation."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base
from app.services.simulation import ScenarioPreset, WeatherSimulator, SCENARIO_META
from app.services.simulation import rainfall_intensity_geojson, flood_area_geojson


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _login(email: str, role: str) -> str:
    client.post("/api/auth/register", json={
        "email": email, "password": "pass123",
        "full_name": email.split("@")[0].title(), "role": role,
    })
    return client.post("/api/auth/login",
                       json={"email": email, "password": "pass123"}).json()["access_token"]


def _ins() -> dict:
    return {"Authorization": f"Bearer {_login('ins@t.com', 'insurer')}"}


def _farmer() -> dict:
    return {"Authorization": f"Bearer {_login('farm@t.com', 'farmer')}"}


def _create_run(scenario: str = "broad_rain") -> dict:
    r = client.post("/api/simulation/runs", json={"scenario": scenario}, headers=_ins())
    assert r.status_code == 201, r.text
    return r.json()


# ── Scenario catalogue ───────────────────────────────────────────────────────

def test_scenarios_list():
    r = client.get("/api/simulation/scenarios")
    assert r.status_code == 200
    items = r.json()
    presets = {s["preset"] for s in items}
    assert {"normal", "broad_rain", "severe_flood", "localised", "faulty_sensor"} == presets
    for s in items:
        assert s["total_ticks"] > 0
        assert s["label"]


# ── Run lifecycle ─────────────────────────────────────────────────────────────

def test_create_run_insurer():
    d = _create_run("severe_flood")
    assert d["scenario"] == "severe_flood"
    assert d["status"] == "paused"
    assert d["current_tick"] == 0
    assert d["total_ticks"] > 0


def test_farmer_cannot_create_run():
    r = client.post("/api/simulation/runs",
                    json={"scenario": "normal"}, headers=_farmer())
    assert r.status_code == 403


def test_farmer_can_read_runs():
    _create_run("normal")
    r = client.get("/api/simulation/runs", headers=_farmer())
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) == 1


# ── Control actions ───────────────────────────────────────────────────────────

def test_start_pause_reset_step():
    run_id = _create_run("broad_rain")["id"]
    h = _ins()

    r = client.post(f"/api/simulation/runs/{run_id}/control", json={"action": "start"}, headers=h)
    assert r.json()["status"] == "running"

    r = client.post(f"/api/simulation/runs/{run_id}/control", json={"action": "pause"}, headers=h)
    assert r.json()["status"] == "paused"

    r = client.post(f"/api/simulation/runs/{run_id}/control", json={"action": "step"}, headers=h)
    assert r.json()["current_tick"] == 1

    r = client.post(f"/api/simulation/runs/{run_id}/control", json={"action": "reset"}, headers=h)
    assert r.json()["current_tick"] == 0
    assert r.json()["status"] == "paused"


def test_invalid_action_returns_400():
    run_id = _create_run("normal")["id"]
    r = client.post(f"/api/simulation/runs/{run_id}/control",
                    json={"action": "fly"}, headers=_ins())
    assert r.status_code == 400


# ── Snapshot ──────────────────────────────────────────────────────────────────

def test_snapshot_structure():
    run_id = _create_run("broad_rain")["id"]
    r = client.get(f"/api/simulation/runs/{run_id}/snapshot", headers=_farmer())
    assert r.status_code == 200
    s = r.json()
    assert s["scenario"] == "broad_rain"
    assert s["tick"] == 0
    assert s["simulated"] is True
    assert len(s["gauge_readings"]) > 0
    assert s["rainfall_geojson"]["type"] == "FeatureCollection"
    assert s["water_geojson"]["type"] == "FeatureCollection"


def test_gauge_readings_change_across_ticks():
    """Different ticks produce different readings (simulation advances)."""
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN)
    s0  = sim.snapshot(0)
    s12 = sim.snapshot(12)
    vals_0  = {r.sensor_id: r.value for r in s0.gauge_readings  if r.sensor_type == "rainfall"}
    vals_12 = {r.sensor_id: r.value for r in s12.gauge_readings if r.sensor_type == "rainfall"}
    different = sum(1 for sid in vals_0 if abs(vals_0[sid] - vals_12.get(sid, 0)) > 0.01)
    assert different > 0


def test_same_seed_reproduces_same_scenario():
    """Fixed seed → identical snapshots every time."""
    sim_a = WeatherSimulator(ScenarioPreset.SEVERE_FLOOD, base_seed=42)
    sim_b = WeatherSimulator(ScenarioPreset.SEVERE_FLOOD, base_seed=42)
    snap_a = sim_a.snapshot(30)
    snap_b = sim_b.snapshot(30)
    assert snap_a.flood_active == snap_b.flood_active
    assert snap_a.flood_intensity == snap_b.flood_intensity
    vals_a = sorted((r.sensor_id, r.value) for r in snap_a.gauge_readings)
    vals_b = sorted((r.sensor_id, r.value) for r in snap_b.gauge_readings)
    assert vals_a == vals_b


def test_flood_scenario_activates_flood_polygon():
    sim = WeatherSimulator(ScenarioPreset.SEVERE_FLOOD)
    total = SCENARIO_META[ScenarioPreset.SEVERE_FLOOD]["total_ticks"]
    flood_snaps = [sim.snapshot(t) for t in range(0, total, 5) if sim.snapshot(t).flood_active]
    assert len(flood_snaps) > 0
    for snap in flood_snaps:
        feat = flood_area_geojson(snap)
        assert feat is not None
        assert feat["geometry"]["type"] == "Polygon"
        ring = feat["geometry"]["coordinates"][0]
        assert ring[0] == ring[-1], "flood polygon ring must be closed"
        assert feat["properties"]["simulated"] is True
        assert "not a verified" in feat["properties"]["note"].lower()


def test_no_flood_in_normal_scenario():
    sim = WeatherSimulator(ScenarioPreset.NORMAL)
    for tick in range(0, sim.total_ticks, 4):
        assert not sim.snapshot(tick).flood_active


def test_faulty_sensor_spike_injected():
    sim = WeatherSimulator(ScenarioPreset.FAULTY_SENSOR)
    faulty = [
        r for tick in range(sim.total_ticks)
        for r in sim.snapshot(tick).gauge_readings
        if r.is_faulty and r.fault_type == "spike"
    ]
    assert len(faulty) > 0
    assert any(r.value > 100 for r in faulty)


def test_localised_scenario_narrow_impact():
    """Localised cell: fewer than half the gauges read high at peak."""
    sim = WeatherSimulator(ScenarioPreset.LOCALISED)
    peak_tick = sim.total_ticks // 2
    snap = sim.snapshot(peak_tick)
    rain = [r.value for r in snap.gauge_readings if r.sensor_type == "rainfall"]
    high = [v for v in rain if v > 30.0]
    assert len(high) < len(rain) / 2


def test_snapshot_geojson_simulated_label():
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN)
    snap = sim.snapshot(10)
    fc = rainfall_intensity_geojson(snap)
    assert fc["properties"]["simulated"] is True
    assert "simulated" in fc["properties"]["note"].lower()
    for feat in fc["features"]:
        assert feat["properties"]["simulated"] is True
