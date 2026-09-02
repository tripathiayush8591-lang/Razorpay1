from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.auth import AdminLoginRequest, AdminLoginResponse, AdminUserResponse
from app.services.auth import authenticate_admin

router = APIRouter(prefix="/api/admin", tags=["admin-auth"])


@router.post("/login", response_model=ApiResponse[AdminLoginResponse])
def admin_login(
    payload: AdminLoginRequest,
    db: Session = Depends(get_db),
) -> ApiResponse[AdminLoginResponse]:
    """Authenticate demo admin user and issue signed 24h bearer token."""
    admin, token = authenticate_admin(db, payload.email, payload.password)
    data = AdminLoginResponse(
        token=token,
        admin=AdminUserResponse.model_validate(admin),
    )
    return ApiResponse(success=True, data=data)


@router.get("/me", response_model=ApiResponse[AdminUserResponse])
def admin_me(
    current_admin: AdminUser = Depends(get_current_admin),
) -> ApiResponse[AdminUserResponse]:
    """Retrieve currently authenticated admin user profile."""
    return ApiResponse(
        success=True,
        data=AdminUserResponse.model_validate(current_admin),
    )
