from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_admin
from app.models.admin_user import AdminUser
from app.schemas.common import ApiResponse
from app.schemas.analytics import AdminAnalyticsResponse
from app.services.analytics import get_admin_analytics

router = APIRouter(prefix="/api/admin/analytics", tags=["admin-analytics"])


@router.get("", response_model=ApiResponse[AdminAnalyticsResponse])
def get_analytics(
    days: Optional[int] = Query(default=None, ge=0, le=365, description="Filter metrics to the last N days (e.g. 7 or 30). Pass 0 or omit for all-time."),
    current_admin: AdminUser = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[AdminAnalyticsResponse]:
    """
    Returns authoritative commerce and agentic analytics for the merchant control center.
    Calculates live KPIs, cart conversions, AI conversations, cross-sell acceptance,
    and channel attribution from SQLite.
    """
    analytics_data = get_admin_analytics(
        db=db,
        merchant_id=current_admin.merchant_id,
        days=days,
    )
    return ApiResponse(success=True, data=analytics_data)
