"""
seed_100_farms.py — Generate 100 farms with farmers, policies, bank accounts.

Deterministic from seed=42. All 100 farms are placed inside the Vidarbha
demo district (Nagpur-Wardha basin) so they appear on the satellite map.

Run AFTER seed_users.py:
  python3 scripts/seed_100_farms.py

Idempotent — safe to re-run (skips existing records by farmer email).
"""
import sys, os, random, uuid
from datetime import date, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.engine import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.models.stage2 import FarmerProfile, Farm, Crop, InsurancePolicy, BankAccountReference
from app.core.security import hash_password
from app.services.geo import DEMO_DISTRICT_BBOX

Base.metadata.create_all(bind=engine)
db = SessionLocal()
rng = random.Random(42)

MIN_LNG, MIN_LAT, MAX_LNG, MAX_LAT = DEMO_DISTRICT_BBOX

# ── Indian names for realistic demo data ─────────────────────────────────────
FIRST_NAMES = [
    "Arjun","Lakshmi","Vikram","Priya","Mohit","Sunita","Ramesh","Anjali",
    "Deepak","Kavita","Suresh","Meena","Ajay","Pooja","Nitin","Rekha",
    "Amit","Geeta","Rahul","Sita","Dinesh","Asha","Manoj","Radha",
    "Vishal","Kamla","Rohit","Saroj","Anil","Usha","Gaurav","Nirmala",
    "Pankaj","Savita","Vinod","Pushpa","Sachin","Lata","Yashpal","Durga",
    "Bharat","Hemlata","Sanjay","Parvati","Ravi","Sudha","Vikas","Santosh",
    "Hemant","Shakuntala","Mukesh","Vimla","Narayan","Champa","Jagdish","Gomati",
    "Kuldeep","Phoolmati","Bhola","Sumitra","Dharam","Kaushalya","Mahesh","Basanti",
    "Chandra","Sulochana","Girish","Rukmini","Hariom","Sarla","Shyam","Indira",
    "Trilok","Shakti","Govind","Leela","Babu","Manju","Ramakant","Chandrawati",
    "Ashok","Prabha","Brij","Vidya","Omprakash","Kusum","Jagannath","Girija",
    "Laxman","Rukmani","Sitaram","Malti","Keshari","Pushplata","Gauri","Bhagwati",
    "Rewati","Ramkali","Dhruv","Shakila",
]

LAST_NAMES = [
    "Singh","Yadav","Verma","Sharma","Patel","Gupta","Mishra","Tiwari",
    "Pandey","Dubey","Chauhan","Rajput","Jha","Thakur","Kumar","Chaudhary",
    "Srivastava","Shukla","Tripathi","Dwivedi",
]

CROPS = [
    ("cotton",    "kharif", (45, 130)), # Signature Vidarbha cash crop ("White Gold")
    ("soybean",   "kharif", (30, 95)),  # Major Vidarbha kharif crop
    ("oranges",   "kharif", (40, 110)), # World-famous Nagpur oranges / citrus
    ("tur",       "kharif", (25, 80)),  # Pigeon pea / Arhar dal
    ("wheat",     "rabi",   (35, 100)),
    ("gram",      "rabi",   (25, 75)),  # Chana / chickpea
    ("rice",      "kharif", (40, 120)),
]

BANKS = [
    ("State Bank of India",   "SBIN0001234"),
    ("Bank of Maharashtra",   "MAHB0000123"), # State-specific leader
    ("Bank of Baroda",        "BARB0000567"),
    ("Punjab National Bank",  "PUNB0056789"),
    ("Canara Bank",           "CNRB0001234"),
    ("Union Bank of India",   "UBIN0567123"),
]

FIELD_TYPES = ["North","South","East","West","Upper","Lower","Riverside","Canal","Village","Main"]
VILLAGES = [
    "Katol","Kalmeshwar","Umred","Saoner","Hingna","Ramtek",
    "Kamptee","Butibori","Seloo","Deoli","Arvi","Narkhed",
    "Bhiwapur","Kuhi","Mouda","Parseoni","Bhandara","Wardha",
]
DISTRICTS = ["Nagpur", "Wardha", "Amravati", "Chandrapur", "Yavatmal"]

# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_point_in_district():
    lat = rng.uniform(MIN_LAT + 0.015, MAX_LAT - 0.015)
    lng = rng.uniform(MIN_LNG + 0.015, MAX_LNG - 0.015)
    return round(lat, 5), round(lng, 5)


def get_or_create_user(email, pw, name, role):
    u = db.query(User).filter(User.email == email).first()
    if not u:
        u = User(email=email, hashed_password=hash_password(pw),
                 full_name=name, role=role)
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


def add_farm_if_new(profile_id, name, lat, lng, area):
    existing = db.query(Farm).filter(
        Farm.farmer_profile_id == profile_id,
        Farm.name == name
    ).first()
    if existing:
        return existing
    f = Farm(farmer_profile_id=profile_id, name=name,
             area_hectares=area, latitude=lat, longitude=lng)
    db.add(f)
    db.flush()
    return f


def add_crop_if_new(farm_id, crop_type, season, area):
    if not db.query(Crop).filter(Crop.farm_id == farm_id).first():
        c = Crop(farm_id=farm_id, crop_type=crop_type,
                 season=season, area_hectares=area)
        db.add(c)
        db.flush()


def add_policy_if_new(farm, profile_id, insurer_id, idx):
    if db.query(InsurancePolicy).filter(InsurancePolicy.farm_id == farm.id).first():
        return
    crop_type, _, (trig_lo, trig_hi) = rng.choice(CROPS)
    trigger = round(rng.uniform(trig_lo, trig_hi), 0)
    full_payout = round(trigger * rng.uniform(2.0, 3.5), 0)
    sum_insured = round(rng.uniform(25000, 150000), 0)
    p = InsurancePolicy(
        policy_number=f"VID-{idx:04d}-{uuid.uuid4().hex[:6].upper()}",
        farm_id=farm.id,
        farmer_profile_id=profile_id,
        insurer_id=insurer_id,
        coverage_start=date(2026, 6, 1),
        coverage_end=date(2026, 10, 31),
        sum_insured=sum_insured,
        rainfall_trigger_mm=trigger,
        rainfall_max_payout_mm=full_payout,
        payout_limit=sum_insured * 0.8,
        status="active",
    )
    db.add(p)
    db.flush()


def add_bank_if_new(profile_id, holder_name):
    if db.query(BankAccountReference).filter(
        BankAccountReference.farmer_profile_id == profile_id
    ).first():
        return
    bank_name, ifsc = rng.choice(BANKS)
    last4 = str(rng.randint(1000, 9999))
    b = BankAccountReference(
        farmer_profile_id=profile_id,
        account_holder_name=holder_name,
        masked_account_number=f"****{last4}",
        bank_name=bank_name,
        ifsc_code=ifsc,
        verification_status="verified",
    )
    db.add(b)
    db.flush()


# ── Main: 100 farmers, 100+ farms inside the district ────────────────────────

insurer = get_or_create_user(
    "insurer@paratrust.dev", "insurer123", "Demo Insurer", UserRole.insurer
)

farm_counter = 0
farmer_count = 0

# Target: 100 farms across 60 farmers (some have 1 farm, some have 2)
for i in range(60):
    fname = rng.choice(FIRST_NAMES)
    lname = rng.choice(LAST_NAMES)
    name  = f"{fname} {lname}"
    email = f"farmer{i+1:03d}@paratrust.dev"
    village = rng.choice(VILLAGES)
    district = rng.choice(DISTRICTS)

    user    = get_or_create_user(email, "farmer123", name, UserRole.farmer)
    profile = get_or_create_profile(
        user.id,
        phone=str(rng.randint(7000000000, 9999999999)),
        address=f"Village {village}, {district}",
        district=district,
        state="Maharashtra",
    )
    add_bank_if_new(profile.id, name)

    # Give ~40 farmers 2 farms, rest get 1 → target ~100 total
    n_farms = 2 if i < 40 else 1
    for j in range(n_farms):
        farm_counter += 1
        lat, lng = rand_point_in_district()
        area     = round(rng.uniform(0.5, 10.0), 1)
        field_label = rng.choice(FIELD_TYPES)
        farm_name   = f"{field_label} Field {farm_counter}"
        farm = add_farm_if_new(profile.id, farm_name, lat, lng, area)
        crop_type, season, _ = rng.choice(CROPS)
        add_crop_if_new(farm.id, crop_type, season, area)
        add_policy_if_new(farm, profile.id, insurer.id, farm_counter)

    farmer_count += 1

db.commit()
db.close()

print(f"✅ Seed complete: {farmer_count} farmers, {farm_counter} farms seeded inside Vidarbha district.")
print(f"   All farms have active parametric policies with varied trigger thresholds.")
