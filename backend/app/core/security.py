import hashlib
from typing import Optional, Dict, Any
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_db
from app.models.admin_user import AdminUser

# Serializer for 24h signed bearer tokens
token_serializer = URLSafeTimedSerializer(settings.AUTH_SECRET_KEY, salt="admin-auth-session")
security_bearer = HTTPBearer(auto_error=False)

TOKEN_MAX_AGE_SECONDS = 86400  # 24 hours


def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash, with fallback for seed sha256."""
    try:
        # Check standard bcrypt
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
            return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        pass

    # Fallback to demo salted sha256 if seeded earlier with fallback
    salt = "runcraft_demo_salt"
    computed = hashlib.sha256(f"{salt}:{plain_password}".encode("utf-8")).hexdigest()
    return computed == hashed_password


def create_access_token(data: Dict[str, Any], expires_seconds: int = TOKEN_MAX_AGE_SECONDS) -> str:
    """Generate a signed, timed token containing admin claims."""
    payload = data.copy()
    return token_serializer.dumps(payload)


def verify_access_token(token: str, max_age: int = TOKEN_MAX_AGE_SECONDS) -> Optional[Dict[str, Any]]:
    """Verify signed token signature and expiration."""
    try:
        data = token_serializer.loads(token, max_age=max_age)
        return data
    except (BadSignature, SignatureExpired):
        return None


def get_current_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    db: Session = Depends(get_db),
) -> AdminUser:
    """FastAPI dependency to authenticate requests with Authorization: Bearer <token>."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header or Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = verify_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired admin session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    admin_id = payload["sub"]
    admin = db.scalar(select(AdminUser).where(AdminUser.id == admin_id))
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin user associated with token no longer exists",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return admin
