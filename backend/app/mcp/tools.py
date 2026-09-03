import uuid
import logging
from typing import Any, Dict, List, Optional

from app.mcp.server import mcp_server, get_db_session, format_mcp_error, record_mcp_audit
from app.schemas.product import ProductResponse
from app.schemas.cart import CartResponse
from app.schemas.checkout import CheckoutInitiateRequest
from app.schemas.order import ShippingAddressSchema
from app.services import catalog, discovery, cart as cart_service, quote as quote_service
from app.services.payment import PaymentService
from app.services import orders as orders_service

logger = logging.getLogger(__name__)


# -------------------------------------------------------------------------
# Tool 1: search_products
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="search_products",
    description="Search active products in the authoritative RunCraft catalog by keyword, category, or maximum price.",
)
def search_products(
    query: Optional[str] = None,
    category: Optional[str] = None,
    max_price_paise: Optional[int] = None,
) -> Dict[str, Any]:
    """Search products in live SQLite catalog."""
    with get_db_session() as db:
        try:
            products = catalog.list_products(
                db=db,
                active_only=True,
                category=category,
                max_price_paise=max_price_paise,
                q=query,
            )
            items = [ProductResponse.from_orm_model(p).model_dump() for p in products]
            result = {
                "count": len(items),
                "products": items,
            }
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="search_products",
                arguments={"query": query, "category": category, "max_price_paise": max_price_paise},
                success=True,
                details=f"Found {len(items)} products",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="search_products",
                arguments={"query": query, "category": category, "max_price_paise": max_price_paise},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 2: get_product
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_product",
    description="Retrieve full specifications, attributes, live price, and inventory for a specific SKU ID.",
)
def get_product(product_id: str) -> Dict[str, Any]:
    """Get authoritative product details by ID."""
    with get_db_session() as db:
        try:
            product = catalog.get_product_by_id(db=db, product_id=product_id, active_only=True)
            result = ProductResponse.from_orm_model(product).model_dump()
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="get_product",
                arguments={"product_id": product_id},
                success=True,
                details=f"Retrieved {product.name}",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="get_product",
                arguments={"product_id": product_id},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 3: check_inventory
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="check_inventory",
    description="Authoritatively verify physical warehouse stock for a product and requested quantity.",
)
def check_inventory(product_id: str, quantity: int = 1) -> Dict[str, Any]:
    """Check physical warehouse inventory."""
    with get_db_session() as db:
        try:
            available, has_stock = discovery.check_inventory(
                db=db,
                product_id=product_id,
                requested_quantity=quantity,
            )
            msg = f"{available} units available in warehouse" if has_stock else f"Only {available} units available (requested {quantity})"
            result = {
                "product_id": product_id,
                "requested_quantity": quantity,
                "available_quantity": available,
                "has_sufficient_stock": has_stock,
                "message": msg,
            }
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="check_inventory",
                arguments={"product_id": product_id, "quantity": quantity},
                success=True,
                details=msg,
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="check_inventory",
                arguments={"product_id": product_id, "quantity": quantity},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 4: get_delivery_estimate
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_delivery_estimate",
    description="Compute delivery timeline and shipping fee based on postal code and cart subtotal.",
)
def get_delivery_estimate(postal_code: str, cart_subtotal_paise: int = 0) -> Dict[str, Any]:
    """Compute delivery estimate and fees."""
    with get_db_session() as db:
        try:
            est = discovery.estimate_delivery(
                db=db,
                subtotal_paise=cart_subtotal_paise,
                postal_code=postal_code,
            )
            result = est.model_dump()
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="get_delivery_estimate",
                arguments={"postal_code": postal_code, "cart_subtotal_paise": cart_subtotal_paise},
                success=True,
            )
            return result
        except Exception as e:
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 5: get_offers
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_offers",
    description="Retrieve active merchant promotional policies, max discount percentage, and delivery rules.",
)
def get_offers() -> Dict[str, Any]:
    """Retrieve active merchant policies and offers."""
    with get_db_session() as db:
        try:
            offers_resp = discovery.get_offers(db=db)
            result = offers_resp.model_dump()
            record_mcp_audit(
                db=db,
                session_id=None,
                tool_name="get_offers",
                arguments={},
                success=True,
            )
            return result
        except Exception as e:
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 6: create_cart
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="create_cart",
    description="Initialize or retrieve an authoritative server-owned cart for an external buyer session.",
)
def create_cart(session_id: Optional[str] = None) -> Dict[str, Any]:
    """Create or get active guest cart."""
    with get_db_session() as db:
        try:
            clean_session = (session_id or "").strip()
            if not clean_session:
                clean_session = f"ext_buyer_{uuid.uuid4().hex[:12]}"
            cart = cart_service.get_or_create_cart(db=db, session_id=clean_session)
            result = CartResponse.from_orm_model(cart).model_dump()
            record_mcp_audit(
                db=db,
                session_id=clean_session,
                tool_name="create_cart",
                arguments={"session_id": clean_session},
                success=True,
                details=f"Cart {cart.id} active",
            )
            return result
        except Exception as e:
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 7: add_to_cart
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="add_to_cart",
    description="Add a validated product and quantity to the external buyer session cart.",
)
def add_to_cart(
    session_id: str,
    cart_id: str,
    product_id: str,
    quantity: int = 1,
) -> Dict[str, Any]:
    """Add item to backend cart."""
    with get_db_session() as db:
        try:
            updated_cart = cart_service.add_to_cart(
                db=db,
                cart_id=cart_id,
                session_id=session_id,
                product_id=product_id,
                quantity=quantity,
            )
            result = CartResponse.from_orm_model(updated_cart).model_dump()
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="add_to_cart",
                arguments={"session_id": session_id, "cart_id": cart_id, "product_id": product_id, "quantity": quantity},
                success=True,
                details=f"Added {quantity} of {product_id} to {cart_id}",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="add_to_cart",
                arguments={"session_id": session_id, "cart_id": cart_id, "product_id": product_id, "quantity": quantity},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 8: remove_from_cart
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="remove_from_cart",
    description="Remove a specific line item from the external buyer session cart.",
)
def remove_from_cart(
    session_id: str,
    cart_id: str,
    item_id: str,
) -> Dict[str, Any]:
    """Remove item from backend cart."""
    with get_db_session() as db:
        try:
            updated_cart = cart_service.remove_from_cart(
                db=db,
                cart_id=cart_id,
                item_id=item_id,
                session_id=session_id,
            )
            result = CartResponse.from_orm_model(updated_cart).model_dump()
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="remove_from_cart",
                arguments={"session_id": session_id, "cart_id": cart_id, "item_id": item_id},
                success=True,
                details=f"Removed {item_id} from {cart_id}",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="remove_from_cart",
                arguments={"session_id": session_id, "cart_id": cart_id, "item_id": item_id},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 9: get_cart
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_cart",
    description="Inspect the current items, quantities, and line amounts of the session cart.",
)
def get_cart(
    session_id: str,
    cart_id: str,
) -> Dict[str, Any]:
    """Get active session cart."""
    with get_db_session() as db:
        try:
            cart = cart_service.get_cart_by_id(db=db, cart_id=cart_id, session_id=session_id)
            result = CartResponse.from_orm_model(cart).model_dump()
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_cart",
                arguments={"session_id": session_id, "cart_id": cart_id},
                success=True,
            )
            return result
        except Exception as e:
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 10: get_final_quote
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_final_quote",
    description="Compute authoritative real-time quote for the cart by re-reading live prices, physical inventory, and delivery fees.",
)
def get_final_quote(
    session_id: str,
    cart_id: str,
) -> Dict[str, Any]:
    """Generate authoritative live price & inventory quote."""
    with get_db_session() as db:
        try:
            quote = quote_service.generate_cart_quote(
                db=db,
                cart_id=cart_id,
                session_id=session_id,
            )
            result = quote.model_dump()
            result["total_inr"] = quote.total_paise / 100
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_final_quote",
                arguments={"session_id": session_id, "cart_id": cart_id},
                success=True,
                details=f"Quote total: ₹{result['total_inr']:.2f}, valid={quote.valid}",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_final_quote",
                arguments={"session_id": session_id, "cart_id": cart_id},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 11: create_checkout
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="create_checkout",
    description="Revalidate quote, freeze immutable order snapshot, and create a Razorpay Test Mode order. Requires explicit human approved_total_paise.",
)
def create_checkout(
    session_id: str,
    cart_id: str,
    approved_total_paise: int,
    customer_name: str,
    customer_email: str,
    customer_phone: str,
    shipping_address: Dict[str, Any],
) -> Dict[str, Any]:
    """Initiate checkout with strict quote revalidation."""
    with get_db_session() as db:
        try:
            shipping = ShippingAddressSchema(**shipping_address)
            checkout_req = CheckoutInitiateRequest(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                shipping_address=shipping,
                approved_total_paise=approved_total_paise,
            )
            checkout_resp = PaymentService.initiate_checkout(
                db=db,
                cart_id=cart_id,
                session_id=session_id,
                checkout_data=checkout_req,
            )
            result = checkout_resp.model_dump()
            result["amount_inr"] = result["amount_paise"] / 100
            result["approval_status"] = "APPROVED"
            result["payment_status"] = "PENDING_PAYMENT"
            result["checkout_url"] = f"http://localhost:5173/checkout?orderId={result['merchant_order_id']}"

            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="create_checkout",
                arguments={
                    "session_id": session_id,
                    "cart_id": cart_id,
                    "approved_total_paise": approved_total_paise,
                    "customer_email": customer_email,
                },
                success=True,
                details=f"Order {result['merchant_order_id']} created for ₹{result['amount_inr']:.2f}",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="create_checkout",
                arguments={
                    "session_id": session_id,
                    "cart_id": cart_id,
                    "approved_total_paise": approved_total_paise,
                },
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 12: get_order
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_order",
    description="Retrieve confirmed order details, immutable line items, and fulfillment tracking.",
)
def get_order(
    session_id: str,
    order_id: str,
) -> Dict[str, Any]:
    """Retrieve full order details with session ownership enforcement."""
    with get_db_session() as db:
        try:
            order = orders_service.get_order_by_id(
                db=db,
                order_id=order_id,
                session_id=session_id,
                allow_admin=False,
            )
            order_resp = orders_service.to_order_response(order)
            result = order_resp.model_dump()
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_order",
                arguments={"session_id": session_id, "order_id": order_id},
                success=True,
                details=f"Retrieved order {order_id} (status={order.status})",
            )
            return result
        except Exception as e:
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_order",
                arguments={"session_id": session_id, "order_id": order_id},
                success=False,
                details=str(e),
            )
            return format_mcp_error(e)


# -------------------------------------------------------------------------
# Tool 13: get_order_status
# -------------------------------------------------------------------------
@mcp_server.tool(
    name="get_order_status",
    description="Poll real-time order fulfillment progress and payment verification state.",
)
def get_order_status(
    session_id: str,
    order_id: str,
) -> Dict[str, Any]:
    """Poll order payment and fulfillment status."""
    with get_db_session() as db:
        try:
            order = orders_service.get_order_by_id(
                db=db,
                order_id=order_id,
                session_id=session_id,
                allow_admin=False,
            )
            order_resp = orders_service.to_order_response(order)
            result = {
                "order_id": order.id,
                "status": order.status,
                "payment_status": order_resp.payment_details.status,
                "paid_at": order.paid_at.isoformat() if order.paid_at else None,
                "fulfillment_status": order.status,
                "carrier": order.carrier,
                "tracking_number": order.tracking_number,
            }
            record_mcp_audit(
                db=db,
                session_id=session_id,
                tool_name="get_order_status",
                arguments={"session_id": session_id, "order_id": order_id},
                success=True,
            )
            return result
        except Exception as e:
            return format_mcp_error(e)
