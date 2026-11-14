"""Stage 3 geographic endpoints: demo district, sensors, water, farm map layers."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.engine import get_db
from app.models.user import UserRole, User
from app.models.stage2 import FarmerProfile, Farm, InsurancePolicy, Crop
from app.models.risk import FarmRiskEstimate
from app.core.deps import require_role
from app.core.security import get_current_user
from app.services import geo
from app.schemas.geo import FarmMapDetail, CropBrief, PolicyBrief

router = APIRouter(prefix="/api/geo", tags=["geo"])


# ── Static / simulated geographic context ────────────────────────────────────

@router.get("/district")
def get_district():
    """Demo district boundary as a single GeoJSON Feature."""
    return geo.district_feature()


@router.get("/sensors")
def get_sensors():
    """Rainfall + water-level gauge locations as a GeoJSON FeatureCollection."""
    return geo.sensors_feature_collection()


@router.get("/water")
def get_water():
    """Rivers and water bodies as a GeoJSON FeatureCollection."""
    return geo.water_feature_collection()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _privacy_safe_label(user: User | None, is_owner: bool = False) -> str:
    if is_owner:
        return "Your farm"
    if not user:
        return "Unknown farmer"
    name = (user.full_name or "").strip()
    if name:
        parts = name.split()
        if len(parts) == 1:
            return parts[0]
        return f"{parts[0]} {parts[-1][0]}."
    # Fall back to a masked email.
    email = user.email or ""
    if "@" in email:
        local, domain = email.split("@", 1)
        local = local[:2] + "***" if len(local) > 2 else local[:1] + "***"
        return f"{local}@{domain}"
    return "Farmer"


def _primary_crop(crops: list[Crop]) -> str | None:
    if not crops:
        return None
    # Prefer the largest cultivated area, else the first.
    ordered = sorted(crops, key=lambda c: (c.area_hectares or 0), reverse=True)
    return ordered[0].crop_type if ordered else None


def _farm_feature(farm: Farm, farmer_label: str, policy: InsurancePolicy | None,
                  is_owner: bool = False) -> dict | None:
    geometry = geo.farm_geometry(farm.latitude, farm.longitude, farm.area_hectares, farm.boundary_geojson)
    if geometry is None:
        return None  # no usable location → omit from the map
    primary_crop = _primary_crop(farm.crops)
    props = {
        "farm_id": farm.id,
        "name": farm.name,
        "area_hectares": farm.area_hectares,
        "farmer_label": farmer_label,
        "primary_crop": primary_crop,
        "policy_status": policy.status if policy else "none",
        "sum_insured": policy.sum_insured if policy else None,
        "is_own": is_owner,
        # Explicit placeholders for later stages:
        "estimated_rainfall_mm": None,
        "risk_category": None,
        "claim_status": None,
        "simulated": False,  # the farm record is real; only the geographic context overlays are simulated
    }
    return {"type": "Feature", "geometry": geometry, "properties": props}


# ── Farm map layers ───────────────────────────────────────────────────────────

@router.get("/farms")
def get_farms(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Farm boundaries as a GeoJSON FeatureCollection.

    Role aware:
      - Farmer: only their own farms (centred-view), labelled "Your farm".
      - Insurer / auditor / admin: all farms within the demo district bbox,
        with privacy-safe farmer labels.
    """
    features: list[dict] = []

    if current_user.role == UserRole.farmer:
        profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
        if not profile:
            return {"type": "FeatureCollection", "features": []}
        farms = db.query(Farm).filter(Farm.farmer_profile_id == profile.id).all()
        for farm in farms:
            policy = _first_active_policy(db, farm.id)
            feat = _farm_feature(farm, "Your farm", policy, is_owner=True)
            if feat:
                feat["properties"]["in_demo_district"] = geo.in_district(farm.latitude, farm.longitude)
                features.append(feat)
        return {"type": "FeatureCollection", "features": features}

    # Insurer / auditor / admin — district view.
    farms = db.query(Farm).all()
    for farm in farms:
        if not geo.in_district(farm.latitude, farm.longitude):
            continue
        label = _privacy_safe_label(farm.farmer_profile.user if farm.farmer_profile else None)
        policy = _first_active_policy(db, farm.id)
        feat = _farm_feature(farm, label, policy, is_owner=False)
        if feat:
            feat["properties"]["in_demo_district"] = True
            features.append(feat)
    return {"type": "FeatureCollection", "features": features}


def _first_active_policy(db: Session, farm_id: int) -> InsurancePolicy | None:
    """Return the most relevant policy for a farm (active preferred, else newest)."""
    policies = db.query(InsurancePolicy).filter(InsurancePolicy.farm_id == farm_id).all()
    if not policies:
        return None
    active = [p for p in policies if p.status == "active"]
    return active[0] if active else policies[0]


# ── Farm detail panel ─────────────────────────────────────────────────────────

@router.get("/farms/{farm_id}", response_model=FarmMapDetail)
def get_farm_detail(
    farm_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Rich farm record for the map detail panel, with explicit placeholders
    for stages not yet built (risk, claim)."""
    farm = db.get(Farm, farm_id)
    if not farm:
        raise HTTPException(status_code=404, detail="Farm not found")

    # Permission: farmers may only view their own farms.
    if current_user.role == UserRole.farmer:
        profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == current_user.id).first()
        if not profile or farm.farmer_profile_id != profile.id:
            raise HTTPException(status_code=403, detail="Access denied")

    profile = farm.farmer_profile
    user = profile.user if profile else None
    is_owner = current_user.role == UserRole.farmer
    farmer_label = _privacy_safe_label(user, is_owner=is_owner)

    policy = _first_active_policy(db, farm.id)
    policy_brief = None
    sum_insured = None
    policy_status = "none"
    if policy:
        policy_brief = PolicyBrief(
            id=policy.id,
            policy_number=policy.policy_number,
            status=policy.status,
            sum_insured=policy.sum_insured,
            coverage_start=str(policy.coverage_start),
            coverage_end=str(policy.coverage_end),
        )
        sum_insured = policy.sum_insured
        policy_status = policy.status

    crops = [
        CropBrief(crop_type=c.crop_type, season=c.season, area_hectares=c.area_hectares)
        for c in (farm.crops or [])
    ]

    risk_est = (
        db.query(FarmRiskEstimate)
        .filter(FarmRiskEstimate.farm_id.in_([str(farm.id), f"SIM-FARM-{farm.id:03d}"]))
        .order_by(FarmRiskEstimate.tick.desc())
        .first()
    )
    estimated_rainfall_mm = risk_est.estimated_rainfall_mm if risk_est else None
    risk_category = risk_est.risk_category if risk_est else None

    stage_notes: list[str] = []
    if not farm.latitude or not farm.longitude:
        stage_notes.append("No coordinates stored for this farm — not shown on the map.")
    if not risk_est:
        stage_notes.append("Risk assessment not yet available (Stage 6).")
    stage_notes.append("Claim tracking not yet available (Stage 8).")

    return FarmMapDetail(
        farm_id=farm.id,
        name=farm.name,
        area_hectares=farm.area_hectares,
        latitude=farm.latitude,
        longitude=farm.longitude,
        farmer_label=farmer_label,
        district=profile.district if profile else None,
        state=profile.state if profile else None,
        crops=crops,
        primary_crop=_primary_crop(farm.crops or []),
        policy=policy_brief,
        policy_status=policy_status,
        sum_insured=sum_insured,
        estimated_rainfall_mm=estimated_rainfall_mm,
        risk_category=risk_category,
        stage_notes=stage_notes,
        in_demo_district=geo.in_district(farm.latitude, farm.longitude),
    )
