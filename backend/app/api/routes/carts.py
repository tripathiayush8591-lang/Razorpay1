from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.product import ProductResponse
from app.schemas.cart import (
    CartCreateRequest,
    CartItemAddRequest,
    CartItemUpdateRequest,
    CartItemResponse,
    CartResponse,
)
from app.schemas.quote import QuoteResponse
from app.schemas.checkout import CheckoutInitiateRequest, CheckoutInitiateResponse
from app.models.cart import Cart
from app.services.cart import (
    get_or_create_cart,
    get_cart_by_id,
    add_to_cart,
    update_cart_item_quantity,
    remove_from_cart,
)
from app.services.quote import generate_cart_quote
from app.services.payment import PaymentService

router = APIRouter(prefix="/api/carts", tags=["carts"])


def resolve_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    session_id: Optional[str] = Query(None),
) -> str:
    """Resolve and validate session ID from either X-Session-ID header or query parameter."""
    resolved = x_session_id or session_id
    if not resolved or not resolved.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session identifier is required (via 'X-Session-ID' header or 'session_id' param)",
        )
    return resolved.strip()


def to_cart_response(cart: Cart) -> CartResponse:
    """Format an ORM Cart into a fully populated CartResponse."""
    items_out = []
    for item in cart.items:
        prod_resp = None
        if item.product:
            prod_resp = ProductResponse.from_orm_model(item.product)
        items_out.append(
            CartItemResponse(
                id=item.id,
                cart_id=item.cart_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price_paise_snapshot=item.unit_price_paise_snapshot,
                product=prod_resp,
                created_at=item.created_at,
                updated_at=item.updated_at,
            )
        )

    return CartResponse(
        id=cart.id,
        merchant_id=cart.merchant_id,
        session_id=cart.session_id,
        status=cart.status,
        currency=cart.currency,
        items=items_out,
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.post("", response_model=ApiResponse[CartResponse])
def create_or_get_cart_endpoint(
    payload: Optional[CartCreateRequest] = None,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Idempotently get or create the active cart for this session."""
    session_id = None
    if payload and payload.session_id.strip():
        session_id = payload.session_id.strip()
    elif x_session_id and x_session_id.strip():
        session_id = x_session_id.strip()

    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID must be provided in request body or X-Session-ID header",
        )

    cart = get_or_create_cart(db, session_id=session_id)
    return ApiResponse(data=to_cart_response(cart))


@router.get("/{cart_id}", response_model=ApiResponse[CartResponse])
def get_cart_endpoint(
    cart_id: str,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Retrieve cart by ID with session ownership verification."""
    cart = get_cart_by_id(db, cart_id=cart_id, session_id=session_id)
    return ApiResponse(data=to_cart_response(cart))


@router.post("/{cart_id}/items", response_model=ApiResponse[CartResponse])
def add_item_endpoint(
    cart_id: str,
    payload: CartItemAddRequest,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Add a product to cart or increment its quantity if already present."""
    cart = add_to_cart(
        db=db,
        cart_id=cart_id,
        session_id=session_id,
        product_id=payload.product_id,
        quantity=payload.quantity,
    )
    return ApiResponse(data=to_cart_response(cart))


@router.patch("/{cart_id}/items/{item_id}", response_model=ApiResponse[CartResponse])
def update_item_quantity_endpoint(
    cart_id: str,
    item_id: str,
    payload: CartItemUpdateRequest,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Authoritatively set item quantity. Quantity=0 removes the item."""
    cart = update_cart_item_quantity(
        db=db,
        cart_id=cart_id,
        item_id=item_id,
        session_id=session_id,
        quantity=payload.quantity,
    )
    return ApiResponse(data=to_cart_response(cart))


@router.delete("/{cart_id}/items/{item_id}", response_model=ApiResponse[CartResponse])
def remove_item_endpoint(
    cart_id: str,
    item_id: str,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Remove a cart item by its cart_item_id."""
    cart = remove_from_cart(
        db=db,
        cart_id=cart_id,
        item_id=item_id,
        session_id=session_id,
    )
    return ApiResponse(data=to_cart_response(cart))


@router.post("/{cart_id}/quote", response_model=ApiResponse[QuoteResponse])
def create_quote_endpoint(
    cart_id: str,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Generate authoritative point-in-time quote revalidating live SQLite prices and inventory."""
    quote = generate_cart_quote(db, cart_id=cart_id, session_id=session_id)
    return ApiResponse(data=quote)


@router.get("/{cart_id}/quote", response_model=ApiResponse[QuoteResponse])
def get_quote_endpoint(
    cart_id: str,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """Convenience endpoint to retrieve authoritative quote for a cart."""
    quote = generate_cart_quote(db, cart_id=cart_id, session_id=session_id)
    return ApiResponse(data=quote)


@router.post("/{cart_id}/checkout", response_model=ApiResponse[CheckoutInitiateResponse])
def checkout_cart_endpoint(
    cart_id: str,
    payload: CheckoutInitiateRequest,
    session_id: str = Depends(resolve_session_id),
    db: Session = Depends(get_db),
):
    """
    Authoritative checkout initiation. Revalidates stock and live prices.
    Creates or reuses internal MerchantOrder and Razorpay Order server-side.
    """
    checkout_res = PaymentService.initiate_checkout(
        db=db,
        cart_id=cart_id,
        session_id=session_id,
        checkout_data=payload,
    )
    return ApiResponse(data=checkout_res)

