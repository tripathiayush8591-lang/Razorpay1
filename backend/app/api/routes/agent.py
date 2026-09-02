from typing import List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.common import ApiResponse
from app.schemas.product import ProductResponse
from app.schemas.cart import CartResponse
from app.schemas.quote import QuoteResponse
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    ToolSearchProductsRequest,
    ToolGetProductRequest,
    ToolAddToCartRequest,
    ToolRemoveFromCartRequest,
    ToolGetQuoteRequest,
    ToolActivityItem,
)
from app.services.agent import process_agent_chat
from app.services.agent_tools import AgentToolExecutor
from app.services.cart import get_or_create_cart, get_cart_by_id

router = APIRouter(prefix="/api/agent", tags=["agent"])


def resolve_agent_session_id(
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    body_session_id: Optional[str] = None,
) -> str:
    """Resolve session ID from header or request body."""
    resolved = x_session_id or body_session_id
    if not resolved or not resolved.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session identifier is required (via 'X-Session-ID' header or session_id in body)",
        )
    return resolved.strip()


@router.post("/chat", response_model=ApiResponse[AgentChatResponse])
def agent_chat(
    data: AgentChatRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """
    Primary conversational endpoint for the in-app AI commerce agent.
    Binds to authoritative guest session and cart.
    Runs Gemini (or deterministic fallback) with live tool execution against SQLite.
    """
    session_id = resolve_agent_session_id(x_session_id, data.session_id)
    response = process_agent_chat(
        db=db,
        session_id=session_id,
        message=data.message,
        cart_id=data.cart_id,
        history=data.history,
    )
    return ApiResponse(data=response)


# -------------------------------------------------------------------------
# Direct Agent Tool REST Routes (as specified in architecture.md)
# -------------------------------------------------------------------------

@router.post("/tools/search-products", response_model=ApiResponse[List[ProductResponse]])
def tool_search_products(
    data: ToolSearchProductsRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Direct agent tool route: Search active products."""
    session_id = resolve_agent_session_id(x_session_id)
    cart = get_or_create_cart(db, session_id=session_id)
    executor = AgentToolExecutor(db=db, session_id=session_id, cart_id=cart.id)
    products = executor.search_products(
        q=data.q,
        category=data.category,
        max_price_paise=data.max_price_paise,
    )
    return ApiResponse(data=[ProductResponse.from_orm_model(p) for p in products])


@router.post("/tools/get-product", response_model=ApiResponse[ProductResponse])
def tool_get_product(
    data: ToolGetProductRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Direct agent tool route: Retrieve product details by ID."""
    session_id = resolve_agent_session_id(x_session_id)
    cart = get_or_create_cart(db, session_id=session_id)
    executor = AgentToolExecutor(db=db, session_id=session_id, cart_id=cart.id)
    product = executor.get_product(product_id=data.product_id)
    return ApiResponse(data=ProductResponse.from_orm_model(product))


@router.post("/tools/add-to-cart", response_model=ApiResponse[CartResponse])
def tool_add_to_cart(
    data: ToolAddToCartRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Direct agent tool route: Add product to session cart."""
    session_id = resolve_agent_session_id(x_session_id)
    executor = AgentToolExecutor(db=db, session_id=session_id, cart_id=data.cart_id)
    updated_cart = executor.add_to_cart(product_id=data.product_id, quantity=data.quantity)
    return ApiResponse(data=CartResponse.from_orm_model(updated_cart))


@router.post("/tools/remove-from-cart", response_model=ApiResponse[CartResponse])
def tool_remove_from_cart(
    data: ToolRemoveFromCartRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Direct agent tool route: Remove product from session cart."""
    session_id = resolve_agent_session_id(x_session_id)
    executor = AgentToolExecutor(db=db, session_id=session_id, cart_id=data.cart_id)
    updated_cart = executor.remove_from_cart(item_id=data.item_id)
    return ApiResponse(data=CartResponse.from_orm_model(updated_cart))


@router.post("/tools/get-final-quote", response_model=ApiResponse[QuoteResponse])
def tool_get_final_quote(
    data: ToolGetQuoteRequest,
    x_session_id: Optional[str] = Header(None, alias="X-Session-ID"),
    db: Session = Depends(get_db),
):
    """Direct agent tool route: Generate authoritative final quote."""
    session_id = resolve_agent_session_id(x_session_id)
    executor = AgentToolExecutor(db=db, session_id=session_id, cart_id=data.cart_id)
    quote = executor.get_final_quote()
    return ApiResponse(data=quote)
