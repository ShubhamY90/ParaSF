"""Stage 3 seed: demo farms clustered inside the Vidarbha demo district.

Run AFTER ``seed_users.py`` (it creates the insurer account used to issue
policies). Idempotent — safe to re-run. Adds ~13 demo farms across 5 demo
farmers, all located within the demo district bounding box so the insurer map
is populated and farm boundaries align with the selected demo area.

Reproducible from the configured simulation seed (see ``settings.simulation_seed``).
"""
import sys, os, random, uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.engine import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.stage2 import FarmerProfile, Farm, Crop, InsurancePolicy, BankAccountReference
from app.core.security import hash_password
from app.services.geo import DEMO_DISTRICT_BBOX, DEMO_DISTRICT_CENTRE
from app.core.config import settings

Base.metadata.create_all(bind=engine)
db = SessionLocal()
rng = random.Random(settings.simulation_seed)

MIN_LNG, MIN_LAT, MAX_LNG, MAX_LAT = DEMO_DISTRICT_BBOX


# ── Helpers ──────────────────────────────────────────────────────────────────
def get_or_create_user(email, pw, name, role):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, hashed_password=hash_password(pw), full_name=name, role=role)
        db.add(u); db.flush()
    return u


def get_or_create_profile(user_id, **kwargs):
    p = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
    if not p:
        p = FarmerProfile(user_id=user_id, **kwargs)
        db.add(p); db.flush()
    return p


def add_farm(profile_id, name, lat, lng, area):
    f = Farm(farmer_profile_id=profile_id, name=name, area_hectares=area,
             latitude=lat, longitude=lng)
    db.add(f); db.flush()
    return f


def add_crop(farm_id, crop_type, season, area):
    c = Crop(farm_id=farm_id, crop_type=crop_type, season=season, area_hectares=area)
    db.add(c); db.flush()
    return c


def add_policy(farm, profile_id, insurer_id, suffix, sum_insured, trigger_mm, max_mm):
    pol_num = f"GEO-{suffix}-{uuid.uuid4().hex[:6].upper()}"
    if db.query(InsurancePolicy).filter(InsurancePolicy.policy_number == pol_num).first():
        return
    p = InsurancePolicy(
        policy_number=pol_num,
        farm_id=farm.id, farmer_profile_id=profile_id, insurer_id=insurer_id,
        coverage_start=date.today(), coverage_end=date.today() + timedelta(days=365),
        sum_insured=sum_insured, rainfall_trigger_mm=trigger_mm,
        rainfall_max_payout_mm=max_mm, payout_limit=sum_insured, status="active",
    )
    db.add(p); db.flush()
    return p


def add_bank(profile_id, holder, last4, bank, ifsc):
    if db.query(BankAccountReference).filter(BankAccountReference.farmer_profile_id == profile_id).first():
        return
    b = BankAccountReference(
        farmer_profile_id=profile_id, account_holder_name=holder,
        masked_account_number=f"****{last4}", bank_name=bank, ifsc_code=ifsc,
        verification_status="verified",
    )
    db.add(b); db.flush()


def rand_point_in_district():
    """Random point inside the demo district bbox (keeps a margin from the edges)."""
    lat = rng.uniform(MIN_LAT + 0.02, MAX_LAT - 0.02)
    lng = rng.uniform(MIN_LNG + 0.02, MAX_LNG - 0.02)
    return round(lat, 5), round(lng, 5)


# ── Insurer (issue policies) ─────────────────────────────────────────────────
insurer = db.query(User).filter(User.email == "insurer@paratrust.dev").first()
if not insurer:
    insurer = get_or_create_user("insurer@paratrust.dev", "insurer123", "Demo Insurer", UserRole.insurer)

# ── Demo farmers within the district ─────────────────────────────────────────
demo_farmers = [
    ("arjun.geo@paratrust.dev",  "farmer123", "Arjun Singh",    "Nagpur", "Maharashtra"),
    ("lakshmi.geo@paratrust.dev","farmer123", "Lakshmi Rao",    "Wardha", "Maharashtra"),
    ("vikram.geo@paratrust.dev", "farmer123", "Vikram Yadav",   "Nagpur", "Maharashtra"),
    ("priya.geo@paratrust.dev",  "farmer123", "Priya Sharma",   "Amravati", "Maharashtra"),
    ("mohit.geo@paratrust.dev",  "farmer123", "Mohit Verma",    "Chandrapur", "Maharashtra"),
]

crop_options = [
    ("wheat", "rabi"), ("rice", "kharif"), ("maize", "kharif"),
    ("sugarcane", "kharif"), ("mustard", "rabi"), ("lentils", "rabi"),
    ("vegetables", "zaid"),
]
farm_name_parts = ["North", "South", "East", "West", "Upper", "Lower", "Riverside", "Canal"]

farm_counter = 0
for email, pw, name, district, state in demo_farmers:
    user = get_or_create_user(email, pw, name, UserRole.farmer)
    profile = get_or_create_profile(user.id, phone=str(rng.randint(9000000000, 9999999999)),
                                    address=f"Village {name.split()[0]}pur", district=district, state=state)
    add_bank(profile.id, name, str(rng.randint(1000, 9999)),
             rng.choice(["State Bank of India", "Bank of Baroda", "Punjab National Bank", "Canara Bank"]),
             rng.choice(["SBIN0001234", "BARB0000567", "PUNB0056789", "CNRB0001234"]))

    n_farms = rng.randint(2, 3)
    for _ in range(n_farms):
        farm_counter += 1
        lat, lng = rand_point_in_district()
        area = round(rng.uniform(1.0, 8.0), 1)
        farm = add_farm(profile.id, f"{rng.choice(farm_name_parts)} Field {farm_counter}", lat, lng, area)
        crop_type, season = rng.choice(crop_options)
        add_crop(farm.id, crop_type, season, area)
        sum_insured = round(rng.uniform(30000, 120000), 0)
        add_policy(farm, profile.id, insurer.id, f"F{farm_counter}",
                   sum_insured, round(rng.uniform(80, 150), 0), round(rng.uniform(250, 400), 0))

db.commit()
db.close()
print(f"Stage-3 geo seed complete: {farm_counter} demo farms added across "
      f"{len(demo_farmers)} farmers inside the Vidarbha demo district.")
