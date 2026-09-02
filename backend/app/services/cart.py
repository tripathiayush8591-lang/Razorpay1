import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.cart import Cart, CartItem
from app.models.merchant import Merchant
from app.services.catalog import get_product_by_id


def verify_cart_ownership(cart: Cart, session_id: str) -> None:
    """Ensure the cart belongs to the requesting session."""
    if not session_id or cart.session_id.strip() != session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Cart does not belong to the current session",
        )


def get_cart_by_id(db: Session, cart_id: str, session_id: Optional[str] = None) -> Cart:
    """Retrieve cart with eager-loaded items and products, verifying session ownership if session_id provided."""
    stmt = (
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .where(Cart.id == cart_id)
    )
    cart = db.scalar(stmt)
    if not cart:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart with ID '{cart_id}' was not found",
        )

    if session_id is not None:
        verify_cart_ownership(cart, session_id)

    return cart


def get_or_create_cart(
    db: Session,
    session_id: str,
    merchant_id: Optional[str] = None,
) -> Cart:
    """Idempotent get-or-create active cart for the given guest session."""
    clean_session_id = session_id.strip()
    if not clean_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id cannot be empty",
        )

    # Search for existing active cart for this session
    stmt = (
        select(Cart)
        .options(joinedload(Cart.items).joinedload(CartItem.product))
        .where(Cart.session_id == clean_session_id, Cart.status == "active")
        .order_by(Cart.created_at.desc())
    )
    cart = db.scalar(stmt)
    if cart:
        return cart

    # Resolve default merchant if not provided
    if not merchant_id:
        merchant = db.scalar(select(Merchant).limit(1))
        if not merchant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No merchant found to associate with cart",
            )
        merchant_id = merchant.id

    now = datetime.now(timezone.utc)
    cart = Cart(
        id=f"cart_{uuid.uuid4().hex[:12]}",
        merchant_id=merchant_id,
        session_id=clean_session_id,
        status="active",
        currency="INR",
        created_at=now,
        updated_at=now,
    )
    db.add(cart)
    db.commit()

    # Re-fetch with relationships populated
    return get_cart_by_id(db, cart.id)


def add_to_cart(
    db: Session,
    cart_id: str,
    session_id: str,
    product_id: str,
    quantity: int = 1,
) -> Cart:
    """Add a product to cart or increment its quantity if already present."""
    if quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quantity to add must be greater than 0",
        )

    cart = get_cart_by_id(db, cart_id, session_id=session_id)
    product = get_product_by_id(db, product_id, active_only=True)

    # Check if item is already in cart
    existing_item = next((item for item in cart.items if item.product_id == product.id), None)
    now = datetime.now(timezone.utc)

    if existing_item:
        existing_item.quantity += quantity
        existing_item.updated_at = now
    else:
        new_item = CartItem(
            id=f"item_{uuid.uuid4().hex[:12]}",
            cart_id=cart.id,
            product_id=product.id,
            quantity=quantity,
            unit_price_paise_snapshot=product.price_paise,
            created_at=now,
            updated_at=now,
        )
        db.add(new_item)

    cart.updated_at = now
    db.commit()

    return get_cart_by_id(db, cart.id)


def update_cart_item_quantity(
    db: Session,
    cart_id: str,
    item_id: str,
    session_id: str,
    quantity: int,
) -> Cart:
    """Set the authoritative quantity of a cart item. If quantity <= 0, remove the item."""
    cart = get_cart_by_id(db, cart_id, session_id=session_id)
    target_item = next((item for item in cart.items if item.id == item_id), None)
    if not target_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cart item with ID '{item_id}' was not found in this cart",
        )

    now = datetime.now(timezone.utc)
    if quantity <= 0:
        db.delete(target_item)
    else:
        target_item.quantity = quantity
        target_item.updated_at = now

    cart.updated_at = now
    db.commit()

    return get_cart_by_id(db, cart.id)


def remove_from_cart(
    db: Session,
    cart_id: str,
    item_id: str,
    session_id: str,
) -> Cart:
    """Remove a cart item by its cart_item_id."""
    return update_cart_item_quantity(
        db=db,
        cart_id=cart_id,
        item_id=item_id,
        session_id=session_id,
        quantity=0,
    )
