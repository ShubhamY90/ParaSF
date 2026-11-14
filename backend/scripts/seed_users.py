"""Seed Stage-2 demo data: 3 farmers with profiles, farms, crops, policies, bank accounts."""
import sys, os, uuid
from datetime import datetime, date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.engine import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.stage2 import FarmerProfile, Farm, Crop, InsurancePolicy, BankAccountReference
from app.core.security import hash_password

# Ensure all tables exist
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# ── Helpers ──────────────────────────────────────────────────────────────────

def get_or_create_user(email, pw, name, role):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, hashed_password=hash_password(pw), full_name=name, role=role)
        db.add(u)
        db.flush()
    return u

def get_or_create_profile(user_id, **kwargs):
    p = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
    if not p:
        p = FarmerProfile(user_id=user_id, **kwargs)
        db.add(p)
        db.flush()
    return p

def add_farm(profile_id, **kwargs):
    f = Farm(farmer_profile_id=profile_id, **kwargs)
    db.add(f)
    db.flush()
    return f

def add_crop(farm_id, **kwargs):
    c = Crop(farm_id=farm_id, **kwargs)
    db.add(c)
    db.flush()
    return c

def add_policy(farm, profile_id, insurer_id, suffix):
    pol_num = f"POL-{suffix}-{uuid.uuid4().hex[:6].upper()}"
    if db.query(InsurancePolicy).filter(InsurancePolicy.policy_number == pol_num).first():
        return  # skip duplicate
    p = InsurancePolicy(
        policy_number=pol_num,
        farm_id=farm.id,
        farmer_profile_id=profile_id,
        insurer_id=insurer_id,
        coverage_start=date.today(),
        coverage_end=date.today() + timedelta(days=365),
        sum_insured=50000.0,
        rainfall_trigger_mm=100.0,
        rainfall_max_payout_mm=300.0,
        payout_limit=50000.0,
        status="active",
    )
    db.add(p)
    db.flush()
    return p

def add_bank(profile_id, holder, last4, bank, ifsc):
    if db.query(BankAccountReference).filter(BankAccountReference.farmer_profile_id == profile_id).first():
        return
    b = BankAccountReference(
        farmer_profile_id=profile_id,
        account_holder_name=holder,
        masked_account_number=f"****{last4}",
        bank_name=bank,
        ifsc_code=ifsc,
        verification_status="pending",
    )
    db.add(b)
    db.flush()

# ── Seed base users ──────────────────────────────────────────────────────────

SEEDS = [
    ("farmer@paratrust.dev",   "farmer123",   "Demo Farmer",    UserRole.farmer),
    ("insurer@paratrust.dev",  "insurer123",  "Demo Insurer",   UserRole.insurer),
    ("auditor@paratrust.dev",  "auditor123",  "Demo Auditor",   UserRole.auditor),
    ("admin@paratrust.dev",    "admin123",    "Platform Admin", UserRole.admin),
]
for email, pw, name, role in SEEDS:
    get_or_create_user(email, pw, name, role)

# Extra insurer and auditor
insurer2 = get_or_create_user("insurer2@paratrust.dev", "insurer123", "Senior Insurer", UserRole.insurer)
auditor2  = get_or_create_user("auditor2@paratrust.dev", "auditor123", "Senior Auditor", UserRole.auditor)

insurer = db.query(User).filter(User.email == "insurer@paratrust.dev").first()

# ── Farmer 1: Rajan Kumar ────────────────────────────────────────────────────

f1 = get_or_create_user("rajan@paratrust.dev", "farmer123", "Rajan Kumar", UserRole.farmer)
p1 = get_or_create_profile(f1.id, phone="9876543210", address="Village Katol, Nagpur", district="Nagpur", state="Maharashtra")

farm1a = add_farm(p1.id, name="North Field", area_hectares=3.5, latitude=21.145, longitude=79.088)
add_crop(farm1a.id, crop_type="cotton", season="kharif", area_hectares=2.0)
add_policy(farm1a, p1.id, insurer.id, "F1A")

farm1b = add_farm(p1.id, name="South Field", area_hectares=2.0, latitude=21.150, longitude=79.092)
add_crop(farm1b.id, crop_type="soybean", season="kharif", area_hectares=2.0)
add_policy(farm1b, p1.id, insurer.id, "F1B")

add_bank(p1.id, "Rajan Kumar", "7890", "Bank of Maharashtra", "MAHB0000123")

# ── Farmer 2: Meena Devi ─────────────────────────────────────────────────────

f2 = get_or_create_user("meena@paratrust.dev", "farmer123", "Meena Devi", UserRole.farmer)
p2 = get_or_create_profile(f2.id, phone="8765432109", address="Taluka Nashik", district="Nashik", state="Maharashtra")

farm2a = add_farm(p2.id, name="Grape Vineyard", area_hectares=5.0, latitude=19.997, longitude=73.789)
add_crop(farm2a.id, crop_type="grapes", season="rabi", area_hectares=5.0)
add_policy(farm2a, p2.id, insurer.id, "F2A")

add_bank(p2.id, "Meena Devi", "2345", "Punjab National Bank", "PUNB0056789")

# ── Farmer 3: Suresh Patel ────────────────────────────────────────────────────

f3 = get_or_create_user("suresh@paratrust.dev", "farmer123", "Suresh Patel", UserRole.farmer)
p3 = get_or_create_profile(f3.id, phone="7654321098", address="Block Anand", district="Anand", state="Gujarat")

farm3a = add_farm(p3.id, name="Cotton Field", area_hectares=8.0, latitude=22.556, longitude=72.951)
add_crop(farm3a.id, crop_type="cotton", season="kharif", area_hectares=8.0)
add_policy(farm3a, p3.id, insurer.id, "F3A")

farm3b = add_farm(p3.id, name="Wheat Plot", area_hectares=4.0, latitude=22.560, longitude=72.955)
add_crop(farm3b.id, crop_type="wheat", season="rabi", area_hectares=4.0)
add_policy(farm3b, p3.id, insurer.id, "F3B")

add_bank(p3.id, "Suresh Patel", "6789", "HDFC Bank", "HDFC0003456")

# ── Commit ───────────────────────────────────────────────────────────────────

db.commit()
db.close()
print("Stage-2 seed complete: 3 demo farmers, farms, crops, policies, bank accounts seeded.")
