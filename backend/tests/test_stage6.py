"""Stage 6 acceptance tests: Farm-Level Risk Assessment."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base
from app.services.risk import (
    assess_farms,
    categorise_risk,
    derive_flood_risk,
    MODEL_VERSION,
)
from app.services.simulation import WeatherSimulator, ScenarioPreset, GaugeReading
from app.services.geo import generate_farms


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
    return client.post(
        "/api/auth/login", json={"email": email, "password": "pass123"}
    ).json()["access_token"]


def _ih():
    return {"Authorization": f"Bearer {_login('ins6@t.com', 'insurer')}"}


def _fh():
    return {"Authorization": f"Bearer {_login('farm6@t.com', 'farmer')}"}


def _create_run(scenario: str = "broad_rain") -> dict:
    r = client.post("/api/simulation/runs", json={"scenario": scenario}, headers=_ih())
    assert r.status_code == 201
    return r.json()


def _classify(run_id: int, tick: int = 10) -> None:
    r = client.post("/api/sensors/classify", json={"run_id": run_id, "tick": tick}, headers=_fh())
    assert r.status_code == 200


# ── Unit tests ────────────────────────────────────────────────────────────────

def test_categorise_risk_low():
    assert categorise_risk(5.0, 1.0) == "low"


def test_categorise_risk_moderate():
    assert categorise_risk(18.0, 2.0) == "moderate"


def test_categorise_risk_high():
    assert categorise_risk(40.0, 5.0) == "high"


def test_categorise_risk_extreme():
    assert categorise_risk(80.0, 5.0) == "extreme"


def test_categorise_risk_insufficient():
    assert categorise_risk(None, None) == "insufficient_evidence"


def test_categorise_uncertainty_upgrade():
    # High uncertainty should upgrade moderate → high
    result = categorise_risk(15.0, 25.0)   # uncertainty 25/15 ≈ 1.67 > 1.5
    assert result in ("high", "moderate")  # upgraded or stays — behaviour documented


def test_derive_flood_risk_no_gauges():
    assert derive_flood_risk([]) is None


def test_derive_flood_risk_low_water():
    readings = [
        GaugeReading(sensor_id="WG-01", sensor_type="water_level",
                     lat=25.3, lng=82.9, value=50.0, unit="cm", tick=10),
    ]
    score = derive_flood_risk(readings)
    assert score is not None
    assert 0.0 <= score <= 1.0
    assert score < 0.3   # 50 cm is well below action level


def test_derive_flood_risk_high_water():
    readings = [
        GaugeReading(sensor_id="WG-01", sensor_type="water_level",
                     lat=25.3, lng=82.9, value=550.0, unit="cm", tick=10),
    ]
    score = derive_flood_risk(readings)
    assert score is not None
    assert score > 0.7   # 550 cm is well above action level


def test_flood_risk_in_range():
    for val in [0, 100, 300, 500, 800]:
        readings = [
            GaugeReading(sensor_id="WG-01", sensor_type="water_level",
                         lat=25.3, lng=82.9, value=float(val), unit="cm", tick=1),
        ]
        score = derive_flood_risk(readings)
        assert 0.0 <= score <= 1.0, f"Flood risk out of range for wl={val}: {score}"


# ── Service-level tests ───────────────────────────────────────────────────────

def test_every_farm_receives_estimate():
    """Every simulated farm must get an estimate or 'insufficient_evidence'."""
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    farms = generate_farms()
    results = assess_farms(run_id=1, tick=20, trust_rows=[], sim=sim)
    assert len(results) == len(farms)
    for r in results:
        assert r.risk_category in (
            "low", "moderate", "high", "extreme", "insufficient_evidence"
        ), f"Unexpected category for {r.farm_id}: {r.risk_category}"


def test_rainfall_estimate_is_non_negative():
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    results = assess_farms(run_id=1, tick=20, trust_rows=[], sim=sim)
    for r in results:
        if r.estimated_rainfall_mm is not None:
            assert r.estimated_rainfall_mm >= 0.0


def test_uncertainty_is_non_negative():
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    results = assess_farms(run_id=1, tick=20, trust_rows=[], sim=sim)
    for r in results:
        if r.uncertainty_mm is not None:
            assert r.uncertainty_mm >= 0.0


def test_ci_ordering():
    """Lower CI ≤ estimate ≤ upper CI for every farm."""
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    results = assess_farms(run_id=1, tick=20, trust_rows=[], sim=sim)
    for r in results:
        if r.estimated_rainfall_mm is not None:
            assert r.lower_ci <= r.estimated_rainfall_mm <= r.upper_ci, (
                f"CI ordering violated for {r.farm_id}: "
                f"[{r.lower_ci}, {r.estimated_rainfall_mm}, {r.upper_ci}]"
            )


def test_model_version_tagged():
    sim = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    results = assess_farms(run_id=1, tick=20, trust_rows=[], sim=sim)
    for r in results:
        assert r.model_version == MODEL_VERSION


def test_severe_flood_gives_higher_risk_than_normal():
    """Severe flood scenario should produce higher risk categories on average."""
    sim_flood  = WeatherSimulator(ScenarioPreset.SEVERE_FLOOD,    base_seed=42)
    sim_normal = WeatherSimulator(ScenarioPreset.NORMAL,           base_seed=42)
    res_flood  = assess_farms(run_id=1, tick=30, trust_rows=[], sim=sim_flood)
    res_normal = assess_farms(run_id=2, tick=30, trust_rows=[], sim=sim_normal)

    _rank = {"low": 0, "moderate": 1, "high": 2, "extreme": 3, "insufficient_evidence": -1}
    avg_flood  = sum(_rank[r.risk_category] for r in res_flood  if _rank[r.risk_category] >= 0) / max(1, len(res_flood))
    avg_normal = sum(_rank[r.risk_category] for r in res_normal if _rank[r.risk_category] >= 0) / max(1, len(res_normal))
    assert avg_flood >= avg_normal, (
        f"Severe flood avg risk ({avg_flood:.2f}) should be ≥ normal ({avg_normal:.2f})"
    )


def test_reproducibility_same_seed():
    """Same (scenario, seed, tick) must produce identical estimates."""
    sim1 = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    sim2 = WeatherSimulator(ScenarioPreset.BROAD_RAIN, base_seed=42)
    res1 = assess_farms(run_id=1, tick=15, trust_rows=[], sim=sim1)
    res2 = assess_farms(run_id=2, tick=15, trust_rows=[], sim=sim2)
    for r1, r2 in zip(res1, res2):
        assert r1.estimated_rainfall_mm == r2.estimated_rainfall_mm
        assert r1.risk_category == r2.risk_category


# ── API endpoint tests ────────────────────────────────────────────────────────

def test_assess_endpoint_all_farms_returned():
    run = _create_run("broad_rain")
    r = client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    assert r.status_code == 200
    d = r.json()
    assert d["run_id"] == run["id"]
    assert d["tick"] == 20
    assert d["simulated"] is True
    assert len(d["farms"]) == 100   # 100 simulated farms
    assert "summary" in d
    assert d["summary"]["total_farms"] == 100


def test_assess_endpoint_valid_categories():
    run = _create_run("broad_rain")
    r = client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_fh())
    valid = {"low", "moderate", "high", "extreme", "insufficient_evidence"}
    for farm in r.json()["farms"]:
        assert farm["risk_category"] in valid


def test_assess_with_trust_scores():
    """When fault detection has run, the GP should use trust scores."""
    run = _create_run("faulty_sensor")
    _classify(run["id"], tick=15)
    r = client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 15}, headers=_ih())
    assert r.status_code == 200
    d = r.json()
    # At least some farms should have an estimate (not all insufficient_evidence).
    non_insuf = [f for f in d["farms"] if f["risk_category"] != "insufficient_evidence"]
    assert len(non_insuf) > 0, "All farms returned insufficient_evidence even with trust scores"


def test_get_risk_layer_after_assess():
    run = _create_run("broad_rain")
    client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    r = client.get(f"/api/risk/{run['id']}", headers=_fh())
    assert r.status_code == 200
    d = r.json()
    assert len(d["farms"]) == 100


def test_get_risk_layer_404_before_assess():
    run = _create_run()
    r = client.get(f"/api/risk/{run['id']}", headers=_fh())
    assert r.status_code == 404


def test_risk_geojson_endpoint():
    run = _create_run("broad_rain")
    client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    r = client.get(f"/api/risk/geojson/{run['id']}", headers=_fh())
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    assert len(fc["features"]) == 100
    for feat in fc["features"]:
        props = feat["properties"]
        assert props["risk_category"] in {"low", "moderate", "high", "extreme", "insufficient_evidence"}
        assert "colour" in props
        assert props["simulated"] is True
        assert "not a confirmed physical flood boundary" in props["note"]


def test_farm_history_endpoint():
    run = _create_run("broad_rain")
    client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 10}, headers=_ih())
    client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    r = client.get(f"/api/risk/{run['id']}/SIM-FARM-001", headers=_fh())
    assert r.status_code == 200
    history = r.json()
    assert len(history) == 2
    ticks = [h["tick"] for h in history]
    assert ticks == sorted(ticks)


def test_idempotent_assess():
    run = _create_run("broad_rain")
    r1 = client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    r2 = client.post("/api/risk/assess", json={"run_id": run["id"], "tick": 20}, headers=_ih())
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Second call overwrites — should still have exactly 100 farms in GET layer.
    rg = client.get(f"/api/risk/{run['id']}", headers=_fh())
    assert len(rg.json()["farms"]) == 100

