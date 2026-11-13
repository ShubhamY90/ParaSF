import enum
from datetime import datetime
from sqlalchemy import String, DateTime, Enum as SAEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.engine import Base

class UserRole(str, enum.Enum):
    farmer = "farmer"
    insurer = "insurer"
    auditor = "auditor"
    admin = "admin"

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), nullable=False, default=UserRole.farmer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Stage 2 relationship – defined here so User.farmer_profile is available.
    # The FarmerProfile model defines the FK; use lazy="joined" so it doesn't
    # break existing queries that don't expect it.
    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False, lazy="select")
