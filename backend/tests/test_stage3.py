"""Stage 3 acceptance tests: satellite map & geographic monitoring."""
import pytest, json
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base

from app.services.geo import DEMO_DISTRICT_BBOX, DEMO_DISTRICT_CENTRE


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)

# A point inside the demo district and one far outside it.
IN_DISTRICT = {"latitude": DEMO_DISTRICT_CENTRE[0], "longitude": DEMO_DISTRICT_CENTRE[1]}
OUTSIDE_DISTRICT = {"latitude": 19.997, "longitude": 73.789}  # Nashik


def make_farmer_with_farm(email, coords, area=3.0, boundary=None, crop="rice", season="kharif", full_name=None):
    name = full_name or email.split("@")[0].title()
    token = register_and_login(email, "farmer", full_name=name)
    h = {"Authorization": f"Bearer {token}"}
    client.post("/api/farmers/profile", json={"district": "Varanasi", "state": "UP"}, headers=h)
    payload = {"name": f"{email.split('@')[0]} plot", "area_hectares": area,
               "latitude": coords["latitude"], "longitude": coords["longitude"]}
    if boundary:
        payload["boundary_geojson"] = boundary
    f = client.post("/api/farmers/farms", json=payload, headers=h).json()
    client.post(f"/api/farmers/farms/{f['id']}/crops",
                json={"crop_type": crop, "season": season, "area_hectares": area}, headers=h)
    return token, h, f


def register_and_login(email: str, role: str, full_name: str | None = None):
    body = {"email": email, "password": "pass123",
            "full_name": full_name or email.split("@")[0].title(), "role": role}
    client.post("/api/auth/register", json=body)
    res = client.post("/api/auth/login", json={"email": email, "password": "pass123"})
    return res.json()["access_token"]


# ── Static geographic context ───────────────────────────────────────────────

def test_district_geojson():
    r = client.get("/api/geo/district")
    assert r.status_code == 200
    f = r.json()
    assert f["type"] == "Feature"
    assert f["geometry"]["type"] == "Polygon"
    assert f["properties"]["name"]
    assert f["properties"]["simulated"] is True
    assert len(f["properties"]["bbox"]) == 4
    # polygon ring is closed
    ring = f["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]


def test_sensors_geojson():
    r = client.get("/api/geo/sensors")
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    types = [feat["properties"]["sensor_type"] for feat in fc["features"]]
    assert types.count("rainfall") == 12
    assert types.count("water_level") == 8  # one gauge per river node
    for feat in fc["features"]:
        assert feat["properties"]["simulated"] is True
        assert feat["geometry"]["type"] == "Point"


def test_water_geojson():
    r = client.get("/api/geo/water")
    assert r.status_code == 200
    fc = r.json()
    kinds = [feat["properties"]["kind"] for feat in fc["features"]]
    assert "river" in kinds
    assert "water_body" in kinds
    river = next(feat for feat in fc["features"] if feat["properties"]["kind"] == "river")
    assert river["geometry"]["type"] == "LineString"
    wb = next(feat for feat in fc["features"] if feat["properties"]["kind"] == "water_body")
    assert wb["geometry"]["type"] == "Polygon"
    for feat in fc["features"]:
        assert feat["properties"]["simulated"] is True


# ── Farm map layers (role-aware) ─────────────────────────────────────────────

def test_farmer_sees_only_own_farms():
    _, h1, f1 = make_farmer_with_farm("own1@test.com", IN_DISTRICT)
    make_farmer_with_farm("other1@test.com", IN_DISTRICT)

    r = client.get("/api/geo/farms", headers=h1)
    assert r.status_code == 200
    fc = r.json()
    assert len(fc["features"]) == 1
    props = fc["features"][0]["properties"]
    assert props["farm_id"] == f1["id"]
    assert props["is_own"] is True
    assert props["farmer_label"] == "Your farm"
    assert props["primary_crop"] == "rice"


def test_insurer_sees_only_district_farms_with_privacy_label():
    make_farmer_with_farm("indist@test.com", IN_DISTRICT, area=4.0, crop="wheat", season="rabi",
                          full_name="Indist Grower")
    # A farm far outside the demo district must NOT appear in the insurer district view.
    make_farmer_with_farm("outdist@test.com", OUTSIDE_DISTRICT, full_name="Away Farmer")

    ins_token = register_and_login("insurer@test.com", "insurer")
    h = {"Authorization": f"Bearer {ins_token}"}
    r = client.get("/api/geo/farms", headers=h)
    assert r.status_code == 200
    fc = r.json()
    # only the in-district farm is present
    assert len(fc["features"]) == 1
    # label is privacy-safe: "Indist G." — first name + last initial, not the full name
    label = fc["features"][0]["properties"]["farmer_label"]
    assert label == "Indist G."
    assert label != "Indist Grower"
    assert fc["features"][0]["properties"]["in_demo_district"] is True
    # real farm records are NOT labelled simulated (only the geographic context overlays are)
    assert fc["features"][0]["properties"]["simulated"] is False


def test_farm_without_coordinates_is_omitted():
    token = register_and_login("nocoord@test.com", "farmer")
    h = {"Authorization": f"Bearer {token}"}
    client.post("/api/farmers/profile", json={"district": "Varanasi"}, headers=h)
    # farm with no lat/lng
    client.post("/api/farmers/farms", json={"name": "no gps", "area_hectares": 2.0}, headers=h)
    r = client.get("/api/geo/farms", headers=h)
    assert r.json()["features"] == []


def test_farm_with_stored_boundary_used_as_is():
    boundary = json.dumps({"type": "Polygon", "coordinates": [[
        [82.95, 25.33], [82.96, 25.33], [82.96, 25.34], [82.95, 25.34], [82.95, 25.33]
    ]]})
    _, h, f = make_farmer_with_farm("boundary@test.com", IN_DISTRICT, boundary=boundary)
    r = client.get("/api/geo/farms", headers=h)
    feat = r.json()["features"][0]
    assert feat["geometry"]["type"] == "Polygon"
    # stored coordinates preserved exactly
    assert feat["geometry"]["coordinates"][0][0] == [82.95, 25.33]


def test_farm_geometry_is_closed_polygon():
    _, h, _ = make_farmer_with_farm("geom@test.com", IN_DISTRICT, area=2.0)
    feat = client.get("/api/geo/farms", headers=h).json()["features"][0]
    ring = feat["geometry"]["coordinates"][0]
    assert ring[0] == ring[-1]
    assert len(ring) == 5  # square: 4 corners + closure


# ── Farm detail panel ────────────────────────────────────────────────────────

def test_farm_detail_correct_record_and_placeholders():
    _, _, f = make_farmer_with_farm("detail@test.com", IN_DISTRICT, area=5.0, crop="maize", season="kharif")
    ins_token = register_and_login("insurer2@test.com", "insurer")
    h = {"Authorization": f"Bearer {ins_token}"}
    r = client.get(f"/api/geo/farms/{f['id']}", headers=h)
    assert r.status_code == 200
    d = r.json()
    assert d["farm_id"] == f["id"]
    assert d["primary_crop"] == "maize"
    assert d["crops"][0]["crop_type"] == "maize"
    # no policy yet in this helper → policy_status none
    assert d["policy_status"] == "none"
    # explicit placeholders for later stages
    assert d["estimated_rainfall_mm"] is None
    assert d["risk_category"] is None
    assert d["claim_status"] is None
    assert any("Stage 6" in n for n in d["stage_notes"])
    assert any("Stage 8" in n for n in d["stage_notes"])


def test_farmer_cannot_view_other_farmer_detail():
    _, _, f1 = make_farmer_with_farm("owner@test.com", IN_DISTRICT)
    _, h2, _ = make_farmer_with_farm("intruder@test.com", IN_DISTRICT)
    r = client.get(f"/api/geo/farms/{f1['id']}", headers=h2)
    assert r.status_code == 403


def test_farmer_can_view_own_farm_detail():
    _, h, f = make_farmer_with_farm("self@test.com", IN_DISTRICT, area=3.0, crop="wheat", season="rabi")
    r = client.get(f"/api/geo/farms/{f['id']}", headers=h)
    assert r.status_code == 200
    assert r.json()["farmer_label"] == "Your farm"
