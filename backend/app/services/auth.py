from typing import Tuple
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.admin_user import AdminUser
from app.core.security import verify_password, create_access_token


def authenticate_admin(db: Session, email: str, password: str) -> Tuple[AdminUser, str]:
    """Authenticate admin credentials and return admin user and signed bearer token."""
    admin = db.scalar(select(AdminUser).where(AdminUser.email == email.strip().lower()))
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, admin.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(
        {
            "sub": admin.id,
            "email": admin.email,
            "role": admin.role,
            "merchant_id": admin.merchant_id,
        }
    )

    return admin, token
