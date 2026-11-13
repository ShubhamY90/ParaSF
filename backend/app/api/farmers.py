"""Farmer-facing endpoints: profile, farms, crops, bank account."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.models.user import UserRole
from app.models.stage2 import FarmerProfile, Farm, Crop, BankAccountReference
from app.schemas.stage2 import (
    FarmerProfileCreate, FarmerProfileUpdate, FarmerProfileOut,
    FarmCreate, FarmOut,
    CropCreate, CropOut,
    BankAccountCreate, BankAccountOut,
)
from app.core.deps import require_role

router = APIRouter(prefix="/api/farmers", tags=["farmers"])

# ── Helper ────────────────────────────────────────────────────────────────────

def _get_profile_or_404(db: Session, user_id: int) -> FarmerProfile:
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return profile


# ── Profile ───────────────────────────────────────────────────────────────────

@router.post("/profile", response_model=FarmerProfileOut, status_code=201)
def upsert_profile(
    body: FarmerProfileCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    """Create or fully update the authenticated farmer's profile."""
    profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
    if profile:
        for field, value in body.model_dump(exclude_unset=True).items():
            setattr(profile, field, value)
    else:
        profile = FarmerProfile(user_id=current_user.id, **body.model_dump())
        db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profile", response_model=FarmerProfileOut)
def get_profile(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    return _get_profile_or_404(db, current_user.id)


# ── Farms ─────────────────────────────────────────────────────────────────────

@router.post("/farms", response_model=FarmOut, status_code=201)
def register_farm(
    body: FarmCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)
    farm = Farm(farmer_profile_id=profile.id, **body.model_dump())
    db.add(farm)
    db.commit()
    db.refresh(farm)
    return farm


@router.get("/farms", response_model=list[FarmOut])
def list_farms(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)
    return db.query(Farm).filter(Farm.farmer_profile_id == profile.id).all()


@router.get("/farms/{farm_id}", response_model=FarmOut)
def get_farm(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)
    farm = db.get(Farm, farm_id)
    if not farm or farm.farmer_profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    return farm


# ── Crops ─────────────────────────────────────────────────────────────────────

@router.post("/farms/{farm_id}/crops", response_model=CropOut, status_code=201)
def add_crop(
    farm_id: int,
    body: CropCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)
    farm = db.get(Farm, farm_id)
    if not farm or farm.farmer_profile_id != profile.id:
        raise HTTPException(status_code=404, detail="Farm not found")
    crop = Crop(farm_id=farm_id, **body.model_dump())
    db.add(crop)
    db.commit()
    db.refresh(crop)
    return crop


# ── Bank Account ──────────────────────────────────────────────────────────────

@router.post("/bank-account", response_model=BankAccountOut, status_code=201)
def submit_bank_account(
    body: BankAccountCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)

    # Mask: keep only last 4 digits
    raw = body.account_number.strip()
    masked = "****" + raw[-4:] if len(raw) >= 4 else "****"

    existing = db.query(BankAccountReference).filter(
        BankAccountReference.farmer_profile_id == profile.id
    ).first()

    if existing:
        existing.account_holder_name = body.account_holder_name
        existing.masked_account_number = masked
        existing.bank_name = body.bank_name
        existing.ifsc_code = body.ifsc_code
        existing.verification_status = "verified"
        existing.verified_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        return existing

    bank = BankAccountReference(
        farmer_profile_id=profile.id,
        account_holder_name=body.account_holder_name,
        masked_account_number=masked,
        bank_name=body.bank_name,
        ifsc_code=body.ifsc_code,
        verification_status="verified",
        verified_at=datetime.utcnow(),
    )
    db.add(bank)
    db.commit()
    db.refresh(bank)
    return bank


@router.get("/bank-account", response_model=BankAccountOut)
def get_bank_account(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.farmer)),
):
    profile = _get_profile_or_404(db, current_user.id)
    bank = db.query(BankAccountReference).filter(
        BankAccountReference.farmer_profile_id == profile.id
    ).first()
    if not bank:
        raise HTTPException(status_code=404, detail="No bank account on file")
    return bank
