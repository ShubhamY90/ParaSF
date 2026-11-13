import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.db.engine import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200

def test_register_and_login():
    r = client.post("/api/auth/register", json={"email": "test@x.com", "password": "pass123", "role": "farmer"})
    assert r.status_code == 201
    r2 = client.post("/api/auth/login", json={"email": "test@x.com", "password": "pass123"})
    assert r2.status_code == 200
    assert r2.json()["role"] == "farmer"

def test_invalid_credentials():
    r = client.post("/api/auth/login", json={"email": "nobody@x.com", "password": "wrong"})
    assert r.status_code == 401

def test_duplicate_email():
    client.post("/api/auth/register", json={"email": "dup@x.com", "password": "pass123"})
    r = client.post("/api/auth/register", json={"email": "dup@x.com", "password": "pass123"})
    assert r.status_code == 400

def test_me_requires_auth():
    r = client.get("/api/auth/me")
    assert r.status_code == 401

def test_me_authenticated():
    client.post("/api/auth/register", json={"email": "me@x.com", "password": "pass123", "role": "insurer"})
    token = client.post("/api/auth/login", json={"email": "me@x.com", "password": "pass123"}).json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["role"] == "insurer"
