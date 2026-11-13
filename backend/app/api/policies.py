"""Policy endpoints (insurer/admin CRUD) and admin farmer-search endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.engine import get_db
from app.models.user import UserRole, User
from app.models.stage2 import InsurancePolicy, FarmerProfile
from app.schemas.stage2 import PolicyCreate, PolicyUpdate, PolicyOut, FarmerProfileOut, FarmerSummary, FarmerDetail
from app.core.deps import require_role
from app.core.security import get_current_user

# ── Policy router ─────────────────────────────────────────────────────────────

router = APIRouter(prefix="/api/policies", tags=["policies"])


def _policy_or_404(db: Session, policy_id: int) -> InsurancePolicy:
    p = db.get(InsurancePolicy, policy_id)
    if not p:
        raise HTTPException(status_code=404, detail="Policy not found")
    return p


@router.post("/", response_model=PolicyOut, status_code=201)
def create_policy(
    body: PolicyCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin)),
):
    if db.query(InsurancePolicy).filter(InsurancePolicy.policy_number == body.policy_number).first():
        raise HTTPException(status_code=400, detail="Policy number already exists")
    policy = InsurancePolicy(insurer_id=current_user.id, **body.model_dump())
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/", response_model=list[PolicyOut])
def list_policies(
    farmer_id: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin, UserRole.auditor)),
):
    q = db.query(InsurancePolicy)
    if farmer_id is not None:
        q = q.filter(InsurancePolicy.farmer_profile_id == farmer_id)
    return q.all()


@router.get("/farmer/{farmer_profile_id}", response_model=list[PolicyOut])
def list_policies_for_farmer(
    farmer_profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # Insurer/admin/auditor can see any farmer; farmer can only see their own
    if current_user.role == UserRole.farmer:
        profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
        if not profile or profile.id != farmer_profile_id:
            raise HTTPException(status_code=403, detail="Access denied")
    return db.query(InsurancePolicy).filter(
        InsurancePolicy.farmer_profile_id == farmer_profile_id
    ).all()


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    policy = _policy_or_404(db, policy_id)
    if current_user.role == UserRole.farmer:
        profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
        if not profile or policy.farmer_profile_id != profile.id:
            raise HTTPException(status_code=403, detail="Access denied")
    return policy


@router.patch("/{policy_id}", response_model=PolicyOut)
def update_policy(
    policy_id: int,
    body: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin)),
):
    policy = _policy_or_404(db, policy_id)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(policy, field, value)
    db.commit()
    db.refresh(policy)
    return policy


# ── Admin farmer-search router ────────────────────────────────────────────────

admin_router = APIRouter(prefix="/api/admin/farmers", tags=["admin"])


@admin_router.get("/", response_model=list[FarmerSummary])
def search_farmers(
    search: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin, UserRole.auditor)),
):
    query_str = search or q
    query = db.query(FarmerProfile).join(User, FarmerProfile.user_id == User.id)
    if query_str:
        like = f"%{query_str}%"
        query = query.filter(
            or_(
                User.full_name.ilike(like),
                User.email.ilike(like),
                FarmerProfile.district.ilike(like),
            )
        )
    profiles = query.all()
    results: list[FarmerSummary] = []
    for p in profiles:
        results.append(
            FarmerSummary(
                id=p.id,
                user_id=p.user_id,
                full_name=p.user.full_name or p.user.email if p.user else "Farmer",
                email=p.user.email if p.user else "",
                phone=p.phone,
                district=p.district,
                state=p.state,
                farm_count=len(p.farms),
                policy_count=len(p.policies),
            )
        )
    return results


@admin_router.get("/{farmer_profile_id}", response_model=FarmerDetail)
def get_farmer_detail(
    farmer_profile_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(UserRole.insurer, UserRole.admin, UserRole.auditor)),
):
    profile = db.get(FarmerProfile, farmer_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Farmer profile not found")
    return FarmerDetail(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.user.full_name or profile.user.email if profile.user else "Farmer",
        email=profile.user.email if profile.user else "",
        phone=profile.phone,
        district=profile.district,
        state=profile.state,
        farm_count=len(profile.farms),
        policy_count=len(profile.policies),
        farms=profile.farms,
        policies=profile.policies,
    )
