"""Seed test accounts for all four roles."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app.db.engine import engine, Base, SessionLocal
from app.models.user import User, UserRole
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)

SEEDS = [
    ("farmer@paratrust.dev",   "farmer123",   "Demo Farmer",    UserRole.farmer),
    ("insurer@paratrust.dev",  "insurer123",  "Demo Insurer",   UserRole.insurer),
    ("auditor@paratrust.dev",  "auditor123",  "Demo Auditor",   UserRole.auditor),
    ("admin@paratrust.dev",    "admin123",    "Platform Admin", UserRole.admin),
]

db = SessionLocal()
for email, pw, name, role in SEEDS:
    if not db.query(User).filter(User.email == email).first():
        db.add(User(email=email, hashed_password=hash_password(pw), full_name=name, role=role))
db.commit()
db.close()
print("Seeded 4 test users.")
