import bcrypt
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.engine import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        pwd_bytes = plain.encode("utf-8")[:72]
        return bcrypt.checkpw(pwd_bytes, hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_minutes)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")

def decode_token(token: str) -> dict:
    # 1. Try local HS256 secret key (backend tokens)
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])
    except JWTError:
        pass

    # 2. Try Firebase ID token (Google RS256 token)
    try:
        claims = jwt.get_unverified_claims(token)
        now = datetime.utcnow().timestamp()
        if "exp" in claims and claims["exp"] < now:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
        if "email" in claims or "sub" in claims:
            return claims
    except HTTPException:
        raise
    except Exception:
        pass

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

def get_user_from_token(token: str, db: Session):
    from app.models.user import User, UserRole
    payload = decode_token(token)
    user_id = payload.get("sub")
    email = payload.get("email")

    user = None
    if user_id is not None and str(user_id).isdigit():
        user = db.get(User, int(user_id))

    if user is None and email:
        user = db.query(User).filter(User.email == str(email).strip().lower()).first()
        if user is None:
            # Auto-provision user in SQLite from Firebase account
            role_map = {
                "farmer@paratrust.dev": UserRole.farmer,
                "insurer@paratrust.dev": UserRole.insurer,
                "auditor@paratrust.dev": UserRole.auditor,
                "admin@paratrust.dev": UserRole.admin,
            }
            role_str = payload.get("role") or role_map.get(str(email).strip().lower()) or UserRole.farmer
            if isinstance(role_str, str):
                try:
                    role = UserRole(role_str)
                except ValueError:
                    role = UserRole.farmer
            else:
                role = role_str

            full_name = payload.get("name") or str(email).split("@")[0]
            user = User(
                email=str(email).strip().lower(),
                hashed_password=hash_password("firebase-auth-managed"),
                full_name=full_name,
                role=role,
                is_active=True,
            )
            db.add(user)
            db.commit()
            db.refresh(user)

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    return get_user_from_token(token, db)
