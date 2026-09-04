from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.product import Product
from app.schemas.agent import ToolActivityItem
from app.schemas.product import ProductResponse
from app.schemas.quote import QuoteResponse
from app.services import catalog, discovery, cart as cart_service, quote as quote_service


class AgentToolExecutor:
    """
    Executes authoritative commerce service actions on behalf of the agent
    and accumulates human-readable tool activities.
    """

    def __init__(self, db: Session, session_id: str, cart_id: str):
        self.db = db
        self.session_id = session_id
        self.cart_id = cart_id
        self.activities: List[ToolActivityItem] = []
        self.latest_order_info: Optional[Dict[str, Any]] = None

    def search_products(
        self,
        q: Optional[str] = None,
        category: Optional[str] = None,
        max_price_paise: Optional[int] = None,
    ) -> List[Product]:
        """Search products in live SQLite catalog."""
        try:
            products = catalog.list_products(
                db=self.db,
                active_only=True,
                category=category,
                max_price_paise=max_price_paise,
                q=q,
            )
            desc_parts = []
            if q:
                desc_parts.append(f"query='{q}'")
            if category:
                desc_parts.append(f"category='{category}'")
            if max_price_paise is not None:
                desc_parts.append(f"max_price=₹{max_price_paise // 100}")
            filter_str = ", ".join(desc_parts) or "all"

            self.activities.append(
                ToolActivityItem(
                    activity=f"search_products({filter_str})",
                    status="completed",
                    details=f"Found {len(products)} matching product(s)",
                )
            )
            return products
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity="search_products()",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def get_product(self, product_id: str) -> Product:
        """Get authoritative product details by ID."""
        try:
            product = catalog.get_product_by_id(db=self.db, product_id=product_id, active_only=True)
            self.activities.append(
                ToolActivityItem(
                    activity=f"get_product(id='{product_id}')",
                    status="completed",
                    details=f"Retrieved {product.name} (₹{product.price_paise // 100})",
                )
            )
            return product
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity=f"get_product('{product_id}')",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def check_inventory(self, product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Authoritatively verify physical stock for a product."""
        try:
            available, has_stock = discovery.check_inventory(
                db=self.db,
                product_id=product_id,
                requested_quantity=quantity,
            )
            status_desc = f"{available} units available" if has_stock else f"Only {available} units available (requested {quantity})"
            self.activities.append(
                ToolActivityItem(
                    activity=f"check_inventory(product_id='{product_id}', qty={quantity})",
                    status="completed" if has_stock else "failed",
                    details=status_desc,
                )
            )
            return {
                "product_id": product_id,
                "requested_quantity": quantity,
                "available_quantity": available,
                "has_sufficient_stock": has_stock,
            }
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity=f"check_inventory('{product_id}')",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def get_related_products(self, product_id: str, limit: int = 4) -> List[Product]:
        """Retrieve related/cross-sell products based on merchant policy."""
        try:
            related = discovery.get_related_products(db=self.db, product_id=product_id, limit=limit)
            self.activities.append(
                ToolActivityItem(
                    activity=f"get_related_products(product_id='{product_id}')",
                    status="completed",
                    details=f"Evaluated cross-sell policy: found {len(related)} related items",
                )
            )
            return related
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity=f"get_related_products('{product_id}')",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def get_offers(self) -> Dict[str, Any]:
        """Retrieve active merchant policies and offers."""
        try:
            offers_resp = discovery.get_offers(db=self.db)
            self.activities.append(
                ToolActivityItem(
                    activity="get_offers()",
                    status="completed",
                    details=f"Checked merchant policies: max discount {offers_resp.max_discount_percent}%",
                )
            )
            return offers_resp.model_dump()
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity="get_offers()",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def add_to_cart(self, product_id: str, quantity: int = 1) -> Cart:
        """Add product to the active session cart."""
        try:
            updated_cart = cart_service.add_to_cart(
                db=self.db,
                cart_id=self.cart_id,
                session_id=self.session_id,
                product_id=product_id,
                quantity=quantity,
            )
            product = catalog.get_product_by_id(db=self.db, product_id=product_id)
            self.activities.append(
                ToolActivityItem(
                    activity=f"add_to_cart(sku='{product.sku}', qty={quantity})",
                    status="completed",
                    details=f"Added {quantity}× {product.name} to cart",
                )
            )
            return updated_cart
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity=f"add_to_cart('{product_id}')",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def remove_from_cart(self, item_id: str) -> Cart:
        """Remove product from the active session cart."""
        try:
            updated_cart = cart_service.remove_from_cart(
                db=self.db,
                cart_id=self.cart_id,
                item_id=item_id,
                session_id=self.session_id,
            )
            self.activities.append(
                ToolActivityItem(
                    activity=f"remove_from_cart(item_id='{item_id}')",
                    status="completed",
                    details=f"Removed item from cart",
                )
            )
            return updated_cart
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity=f"remove_from_cart('{item_id}')",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def get_final_quote(self) -> QuoteResponse:
        """Generate authoritative live price & inventory quote for the active cart."""
        try:
            quote_resp = quote_service.generate_cart_quote(
                db=self.db,
                cart_id=self.cart_id,
                session_id=self.session_id,
            )
            total_inr = quote_resp.total_paise / 100
            self.activities.append(
                ToolActivityItem(
                    activity="get_final_quote()",
                    status="completed" if quote_resp.valid else "failed",
                    details=f"Authoritative total: ₹{total_inr:,.2f} ({len(quote_resp.items)} items, valid={quote_resp.valid})",
                )
            )
            return quote_resp
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity="get_final_quote()",
                    status="failed",
                    details=str(e),
                )
            )
            raise e

    def get_order_status(self) -> Dict[str, Any]:
        """Retrieve authoritative order status for the current guest session."""
        try:
            import json
            from app.services.orders import list_guest_orders
            orders = list_guest_orders(self.db, session_id=self.session_id)
            if not orders:
                self.activities.append(
                    ToolActivityItem(
                        activity="check_order_status()",
                        status="completed",
                        details="No orders found for current session",
                    )
                )
                self.latest_order_info = {"has_orders": False, "orders": []}
                return self.latest_order_info

            latest = orders[0]

            # Parse line items snapshot for rich summary
            items_summary = ""
            items_count = 0
            try:
                snapshot = json.loads(latest.items_snapshot_json or "[]")
                items_count = sum(item.get("quantity", 1) for item in snapshot)
                names = [item.get("name", "Item") for item in snapshot]
                items_summary = ", ".join(names[:2]) + ("..." if len(names) > 2 else "")
            except Exception:
                pass

            self.activities.append(
                ToolActivityItem(
                    activity=f"check_order_status(order_id='{latest.id}')",
                    status="completed",
                    details=f"Status: {latest.status}",
                )
            )
            order_data = {
                "has_orders": True,
                "order_id": latest.id,
                "status": latest.status,
                "carrier": latest.carrier,
                "tracking_number": latest.tracking_number,
                "amount_paise": latest.amount_paise,
                "customer_name": latest.customer_name,
                "created_at": latest.created_at.isoformat() if latest.created_at else None,
                "items_count": items_count,
                "items_summary": items_summary,
            }
            self.latest_order_info = order_data
            return order_data
        except Exception as e:
            self.activities.append(
                ToolActivityItem(
                    activity="check_order_status()",
                    status="failed",
                    details=str(e),
                )
            )
            self.latest_order_info = {"has_orders": False, "error": str(e)}
            return self.latest_order_info
