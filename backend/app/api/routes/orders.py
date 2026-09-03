from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.order import OrderResponse
from app.services.orders import get_order_by_id, list_guest_orders, to_order_response
from app.core.security import verify_access_token

router = APIRouter(prefix="/api/orders", tags=["orders"])


def resolve_optional_admin(authorization: Optional[str] = Header(None)) -> bool:
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:].strip()
        payload = verify_access_token(token)
        return payload is not None and "sub" in payload
    return False


@router.get("", response_model=ApiResponse[List[OrderResponse]])
def get_guest_orders_endpoint(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieves all orders placed within the current guest session.
    Enforces strict guest-session isolation.
    """
    if not x_session_id or not x_session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session identifier is required via 'X-Session-ID' header",
        )

    orders = list_guest_orders(db=db, session_id=x_session_id.strip())
    data = [to_order_response(o) for o in orders]
    return ApiResponse(data=data)



@router.get("/{order_id}", response_model=ApiResponse[OrderResponse])
def get_order_endpoint(
    order_id: str,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    is_admin: bool = Depends(resolve_optional_admin),
    db: Session = Depends(get_db),
):
    """
    Retrieves an order by ID.
    Enforces strict guest-session isolation (cannot view other session's order unless authenticated admin).
    """
    if not is_admin and (not x_session_id or not x_session_id.strip()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session identifier is required via 'X-Session-ID' header",
        )

    order = get_order_by_id(
        db=db,
        order_id=order_id,
        session_id=x_session_id.strip() if x_session_id else None,
        allow_admin=is_admin,
    )
    return ApiResponse(data=to_order_response(order))
