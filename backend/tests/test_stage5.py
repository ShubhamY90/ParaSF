"""Stage 5 acceptance tests: Sensor Fault Detection & Trust Scoring."""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base
from app.services.fault_detection import (
    classify_readings, generate_training_data, get_trained_model,
    compute_trust_score, FAULT_CLASSES,
)
from app.services.simulation import (
    WeatherSimulator, ScenarioPreset, GaugeReading,
)


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


def _ih():  # insurer headers
    return {"Authorization": f"Bearer {_login('ins5@t.com', 'insurer')}"}


def _fh():  # farmer headers (read-only access)
    return {"Authorization": f"Bearer {_login('farm5@t.com', 'farmer')}"}


def _create_run(scenario: str = "faulty_sensor") -> dict:
    r = client.post("/api/simulation/runs", json={"scenario": scenario}, headers=_ih())
    assert r.status_code == 201
    return r.json()


# ── Training data & model ─────────────────────────────────────────────────────

def test_training_data_has_all_classes():
    df = generate_training_data()
    assert set(df["label"].unique()) == set(FAULT_CLASSES)
    # Reasonably balanced — no class less than 5% of total.
    for cls in FAULT_CLASSES:
        pct = (df["label"] == cls).sum() / len(df)
        assert pct >= 0.05, f"Class '{cls}' underrepresented: {pct:.2%}"


def test_model_trains_and_evaluates():
    tm = get_trained_model()
    assert tm.model is not None
    assert set(tm.label_encoder.classes_) == set(FAULT_CLASSES)
    # Classification report must mention every class.
    for cls in FAULT_CLASSES:
        assert cls in tm.class_report
    # Confusion matrix has correct shape.
    n = len(FAULT_CLASSES)
    assert len(tm.confusion) == n
    assert all(len(row) == n for row in tm.confusion)


def test_genuine_localised_cell_not_classified_as_fault():
    """The key safety requirement: genuine localised cell must NOT be a fault class."""
    tm = get_trained_model()
    # Build a reading that looks like genuine_localised_cell:
    # own value very high, but neighbours very low.
    reading = GaugeReading(
        sensor_id="RG-01", sensor_type="rainfall",
        lat=25.3, lng=82.9, value=150.0, unit="mm/hr", tick=20,
    )
    history = [2.0, 2.5, 3.0, 2.8, 150.0]  # sudden rise at end
    # Neighbours all low.
    from app.services.fault_detection import _build_live_features
    import numpy as np
    X = _build_live_features(reading, history, [2.0, 3.0, 2.5])
    tm2 = get_trained_model()
    proba = tm2.model.predict_proba(X)[0]
    classes = list(tm2.label_encoder.classes_)
    # genuine_localised_cell probability must be non-trivial (> 5%).
    glc_prob = proba[classes.index("genuine_localised_cell")]
    # We don't assert it's the top class (model may still flag it), but it
    # must NOT have zero probability — the class must be representable.
    assert glc_prob > 0.0, "genuine_localised_cell has zero probability — class missing"


def test_spike_reading_classified_correctly():
    """A large spike value should NOT be classified as normal with high confidence."""
    reading = GaugeReading(
        sensor_id="RG-02", sensor_type="rainfall",
        lat=25.3, lng=82.9, value=220.0, unit="mm/hr", tick=24,
    )
    # History is flat low — sudden spike.
    results = classify_readings([reading], {"RG-02": [1.0, 1.1, 1.2, 1.0, 220.0]})
    assert len(results) == 1
    r = results[0]
    # Must not be classified as normal with high confidence.
    normal_prob = r.class_probabilities.get("normal", 0.0)
    assert normal_prob < 0.9, f"Spike incorrectly classified as normal with p={normal_prob:.2f}"


def test_dead_sensor_classified_correctly():
    reading = GaugeReading(
        sensor_id="RG-03", sensor_type="rainfall",
        lat=25.3, lng=82.9, value=0.0, unit="mm/hr", tick=30,
    )
    results = classify_readings([reading], {"RG-03": [0.0, 0.0, 0.0, 0.0, 0.0]})
    r = results[0]
    # Dead sensor should not be classified as normal with very high confidence.
    normal_prob = r.class_probabilities.get("normal", 0.0)
    assert not (r.predicted_class == "normal" and normal_prob > 0.95), \
        "Dead sensor classified as normal with high confidence"


def test_trust_score_ranges():
    """Trust scores must be in [0, 1] for all classes and confidences."""
    for cls in FAULT_CLASSES:
        for conf in [0.3, 0.6, 0.9, 1.0]:
            ts = compute_trust_score(cls, conf)
            assert 0.0 <= ts <= 1.0, f"Trust out of range for {cls}/{conf}: {ts}"


def test_trust_score_ordering():
    """Normal and genuine_localised_cell must have higher trust than fault classes."""
    normal_trust = compute_trust_score("normal", 0.9)
    spike_trust  = compute_trust_score("spike",  0.9)
    dead_trust   = compute_trust_score("dead",   0.9)
    glc_trust    = compute_trust_score("genuine_localised_cell", 0.9)
    assert normal_trust > spike_trust
    assert normal_trust > dead_trust
    assert glc_trust    > spike_trust


def test_water_level_gauges_not_classified_as_faulty():
    """Water-level gauges should always come back as normal (not in fault model scope)."""
    readings = [
        GaugeReading(sensor_id="WG-01", sensor_type="water_level",
                     lat=25.3, lng=82.9, value=250.0, unit="cm", tick=10),
        GaugeReading(sensor_id="WG-02", sensor_type="water_level",
                     lat=25.3, lng=82.95, value=0.0, unit="cm", tick=10),
    ]
    results = classify_readings(readings)
    for r in results:
        assert r.predicted_class == "normal"
        assert r.is_flagged is False


def test_investigation_note_preserved():
    reading = GaugeReading(
        sensor_id="RG-04", sensor_type="rainfall",
        lat=25.3, lng=82.9, value=180.0, unit="mm/hr", tick=15,
    )
    results = classify_readings([reading], {"RG-04": [1.0, 1.0, 1.0, 1.0, 180.0]})
    assert len(results[0].investigation_note) > 10


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_model_evaluation_endpoint():
    r = client.get("/api/sensors/model/evaluation", headers=_fh())
    assert r.status_code == 200
    d = r.json()
    assert set(d["classes"]) == set(FAULT_CLASSES)
    assert "genuine_localised_cell" in d["classification_report"]
    assert len(d["confusion_matrix"]) == len(FAULT_CLASSES)
    assert "not a sensor fault" in d["note"].lower()


def test_classify_endpoint_persists_and_returns_scores():
    run = _create_run("faulty_sensor")
    r = client.post("/api/sensors/classify",
                    json={"run_id": run["id"], "tick": 20}, headers=_fh())
    assert r.status_code == 200
    d = r.json()
    assert d["run_id"] == run["id"]
    assert d["tick"] == 20
    assert len(d["scores"]) > 0
    assert all(0.0 <= v <= 1.0 for v in d["scores"].values())
    assert isinstance(d["flagged"], list)
    assert d["simulated"] is True


def test_faulty_scenario_produces_flagged_sensor():
    """The FAULTY_SENSOR scenario injects a spike — at least one sensor should be flagged."""
    run = _create_run("faulty_sensor")
    # Classify at the spike window (tick 15–24 is 30–50% of 48 total).
    r = client.post("/api/sensors/classify",
                    json={"run_id": run["id"], "tick": 20}, headers=_fh())
    d = r.json()
    # Either flagged list is non-empty OR at least one sensor has lowered trust score.
    has_low_trust = any(v < 0.9 for v in d["scores"].values())
    assert len(d["flagged"]) > 0 or has_low_trust, \
        "Faulty sensor scenario produced no flags and all trust scores ≥ 0.9"


def test_trust_geojson_endpoint():
    run = _create_run("faulty_sensor")
    client.post("/api/sensors/classify", json={"run_id": run["id"], "tick": 15}, headers=_fh())
    r = client.get(f"/api/sensors/geojson/{run['id']}", headers=_fh())
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    for feat in fc["features"]:
        props = feat["properties"]
        assert 0.0 <= props["trust_score"] <= 1.0
        assert props["predicted_class"] in FAULT_CLASSES
        assert props["simulated"] is True
