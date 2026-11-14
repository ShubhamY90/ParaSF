from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.engine import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserSync, UserOut, LoginRequest, TokenResponse
from app.core.security import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=UserOut, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/sync", response_model=UserOut)
def sync_user(body: UserSync, db: Session = Depends(get_db)):
    """Sync or provision a user from Firebase Auth into SQLite DB with their designated role."""
    email_clean = body.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if user:
        if body.full_name and not user.full_name:
            user.full_name = body.full_name
        if body.role and user.role != body.role:
            user.role = body.role
    else:
        user = User(
            email=email_clean,
            hashed_password=hash_password("firebase-auth-managed"),
            full_name=body.full_name,
            role=body.role,
            is_active=True,
        )
        db.add(user)
    db.commit()
    db.refresh(user)
    return user

@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account inactive")
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(access_token=token, role=user.role, user_id=user.id, full_name=user.full_name)

@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user
