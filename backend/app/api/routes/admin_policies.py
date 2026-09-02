from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.policy import MerchantPolicyResponse, MerchantPolicyUpdateRequest
from app.services.policy import get_merchant_policy, update_merchant_policy

router = APIRouter(prefix="/api/admin/policies", tags=["admin-policies"])


@router.get("", response_model=ApiResponse[MerchantPolicyResponse])
def get_policies(
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MerchantPolicyResponse]:
    """Retrieve authoritative merchant policies."""
    policy = get_merchant_policy(db=db, merchant_id=current_admin.merchant_id)
    return ApiResponse(success=True, data=MerchantPolicyResponse.from_orm_model(policy))


@router.put("", response_model=ApiResponse[MerchantPolicyResponse])
def update_policies(
    payload: MerchantPolicyUpdateRequest,
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MerchantPolicyResponse]:
    """Update merchant policies including editable cross-sell pairings and delivery thresholds."""
    updated = update_merchant_policy(
        db=db,
        merchant_id=current_admin.merchant_id,
        data=payload,
    )
    return ApiResponse(success=True, data=MerchantPolicyResponse.from_orm_model(updated))
