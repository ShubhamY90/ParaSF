import pytest
from datetime import date
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def register_and_login(email: str, role: str):
    client.post("/api/auth/register", json={"email": email, "password": "pass123", "full_name": email.split("@")[0], "role": role})
    res = client.post("/api/auth/login", json={"email": email, "password": "pass123"})
    return res.json()["access_token"]

def test_farmer_profile_and_farm_creation():
    farmer_token = register_and_login("farmer1@test.com", "farmer")
    headers = {"Authorization": f"Bearer {farmer_token}"}

    # Profile upsert
    p_res = client.post("/api/farmers/profile", json={"phone": "+91-9876543210", "district": "Varanasi", "state": "UP"}, headers=headers)
    assert p_res.status_code in (200, 201)
    p_data = p_res.json()
    assert p_data["district"] == "Varanasi"

    # Farm creation
    f_res = client.post("/api/farmers/farms", json={"name": "Ganga Basin Plot", "area_hectares": 3.5, "latitude": 25.3176, "longitude": 82.9739}, headers=headers)
    assert f_res.status_code == 201
    f_data = f_res.json()
    farm_id = f_data["id"]
    assert f_data["name"] == "Ganga Basin Plot"

    # Crop addition
    c_res = client.post(f"/api/farmers/farms/{farm_id}/crops", json={"crop_type": "rice", "season": "kharif", "area_hectares": 3.5}, headers=headers)
    assert c_res.status_code == 201
    assert c_res.json()["crop_type"] == "rice"

    # Bank account submission (masked)
    b_res = client.post("/api/farmers/bank-account", json={"account_holder_name": "Farmer One", "account_number": "12345678901234", "bank_name": "State Bank of India", "ifsc_code": "SBIN0001234"}, headers=headers)
    assert b_res.status_code in (200, 201)
    b_data = b_res.json()
    assert b_data["masked_account_number"] == "****1234"
    assert b_data["verification_status"] == "verified"

def test_insurer_policy_management_and_isolation():
    farmer1_token = register_and_login("farmerA@test.com", "farmer")
    farmer2_token = register_and_login("farmerB@test.com", "farmer")
    insurer_token = register_and_login("insurer@test.com", "insurer")

    h1 = {"Authorization": f"Bearer {farmer1_token}"}
    h2 = {"Authorization": f"Bearer {farmer2_token}"}
    h_ins = {"Authorization": f"Bearer {insurer_token}"}

    # Farmer 1 creates profile & farm
    client.post("/api/farmers/profile", json={"district": "Nashik"}, headers=h1)
    f1_res = client.post("/api/farmers/farms", json={"name": "Vineyard A", "area_hectares": 4.0}, headers=h1)
    f1_id = f1_res.json()["id"]

    # Farmer 2 creates profile & farm
    p2 = client.post("/api/farmers/profile", json={"district": "Pune"}, headers=h2).json()
    f2_res = client.post("/api/farmers/farms", json={"name": "Field B", "area_hectares": 2.5}, headers=h2)
    f2_id = f2_res.json()["id"]

    # Insurer creates policy for Farmer 1
    pol_payload = {
        "policy_number": "PT-2026-NASHIK-001",
        "farm_id": f1_id,
        "farmer_profile_id": f1_res.json()["farmer_profile_id"],
        "coverage_start": "2026-06-01",
        "coverage_end": "2026-11-30",
        "sum_insured": 150000.0,
        "rainfall_trigger_mm": 180.0,
        "rainfall_max_payout_mm": 350.0,
        "status": "active"
    }
    pol_res = client.post("/api/policies/", json=pol_payload, headers=h_ins)
    assert pol_res.status_code == 201
    pol_id = pol_res.json()["id"]

    # Insurer searches farmers
    search_res = client.get("/api/admin/farmers/?search=Nashik", headers=h_ins)
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # Farmer 1 can see their policy
    f1_pol_res = client.get(f"/api/policies/{pol_id}", headers=h1)
    assert f1_pol_res.status_code == 200
    assert f1_pol_res.json()["policy_number"] == "PT-2026-NASHIK-001"

    # Farmer 2 CANNOT see Farmer 1's policy (isolated)
    f2_pol_res = client.get(f"/api/policies/{pol_id}", headers=h2)
    assert f2_pol_res.status_code == 403

    # Farmer cannot create policy (only insurer/admin)
    forbidden_pol = client.post("/api/policies/", json=pol_payload, headers=h1)
    assert forbidden_pol.status_code == 403
