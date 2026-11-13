"""Stage 2 ORM models: FarmerProfile, Farm, Crop, InsurancePolicy, PolicyRule, BankAccountReference."""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.engine import Base


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    district: Mapped[str | None] = mapped_column(String(255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="farmer_profile")
    farms = relationship("Farm", back_populates="farmer_profile", cascade="all, delete-orphan")
    bank_account = relationship("BankAccountReference", back_populates="farmer_profile",
                                uselist=False, cascade="all, delete-orphan")
    policies = relationship("InsurancePolicy", back_populates="farmer_profile")


class Farm(Base):
    __tablename__ = "farms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmer_profiles.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    boundary_geojson: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    farmer_profile = relationship("FarmerProfile", back_populates="farms")
    crops = relationship("Crop", back_populates="farm", cascade="all, delete-orphan")
    policies = relationship("InsurancePolicy", back_populates="farm")


class Crop(Base):
    __tablename__ = "crops"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(255), nullable=False)
    season: Mapped[str | None] = mapped_column(String(100), nullable=True)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationships
    farm = relationship("Farm", back_populates="crops")


class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    farm_id: Mapped[int] = mapped_column(Integer, ForeignKey("farms.id"), nullable=False)
    farmer_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmer_profiles.id"), nullable=False)
    insurer_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    coverage_start: Mapped[datetime] = mapped_column(Date, nullable=False)
    coverage_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    sum_insured: Mapped[float] = mapped_column(Float, nullable=False)
    rainfall_trigger_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    rainfall_max_payout_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    flood_trigger_level: Mapped[float | None] = mapped_column(Float, nullable=True)
    payout_limit: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    farm = relationship("Farm", back_populates="policies")
    farmer_profile = relationship("FarmerProfile", back_populates="policies")
    insurer = relationship("User", foreign_keys=[insurer_id])
    rules = relationship("PolicyRule", back_populates="policy", cascade="all, delete-orphan")


class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("insurance_policies.id"), nullable=False)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_value: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    policy = relationship("InsurancePolicy", back_populates="rules")


class BankAccountReference(Base):
    __tablename__ = "bank_account_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    farmer_profile_id: Mapped[int] = mapped_column(Integer, ForeignKey("farmer_profiles.id"),
                                                    unique=True, nullable=False)
    account_holder_name: Mapped[str] = mapped_column(String(255), nullable=False)
    masked_account_number: Mapped[str] = mapped_column(String(20), nullable=False)
    bank_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ifsc_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    verification_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    farmer_profile = relationship("FarmerProfile", back_populates="bank_account")
