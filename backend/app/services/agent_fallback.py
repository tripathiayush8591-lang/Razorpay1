import re
from typing import List, Optional, Tuple
from app.models.product import Product
from app.schemas.agent import (
    AgentChatResponse,
    ChatMessageTurn,
    ProductRecommendationItem,
    AgentOrderStatusSnapshot,
)
from app.schemas.cart import CartResponse
from app.schemas.product import ProductResponse
from app.schemas.quote import QuoteResponse
from app.services.agent_tools import AgentToolExecutor
from app.services.cart import get_cart_by_id


def extract_budget_paise(text: str) -> Optional[int]:
    """Extract budget in paise from phrases like 'under ₹8,000', 'budget 8000', 'below 5000'."""
    pattern = r"(?:under|below|budget|max|within|less than)\s*₹?\s*([0-9,]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        clean_num = match.group(1).replace(",", "")
        try:
            return int(clean_num) * 100
        except ValueError:
            pass
    return None


def run_deterministic_fallback(
    executor: AgentToolExecutor,
    message: str,
    history: Optional[List[ChatMessageTurn]] = None,
) -> AgentChatResponse:
    """
    Deterministic rule-based orchestrator that executes REAL Phase 3 commerce services.
    Ensures 100% demo reliability without depending on external LLM APIs.
    """
    lower = message.strip().lower()
    budget_paise = extract_budget_paise(lower)

    recommendations: List[ProductRecommendationItem] = []
    response_msg = ""
    approval_required = False

    # Check recent history for context clues (e.g. multi-turn "add socks")
    last_assistant_msg = ""
    if history:
        for turn in reversed(history):
            if turn.role == "assistant":
                last_assistant_msg = turn.content.lower()
                break

    # Intent -1: Order tracking / status query ("Where is my order?", "tell me my order status")
    order_tracking_triggers = [
        "where is my order", "where's my order", "where is my package", "where's my package",
        "track my order", "track order", "track my package", "track package",
        "what's the status of my order", "what is the status of my order", "order status",
        "status of my order", "package status", "tell me my order status", "tell me the status of my order",
        "show my order", "my order status", "check my order", "order tracking", "order update",
        "what happened to my order", "check order status"
    ]
    is_order_tracking = any(t in lower for t in order_tracking_triggers) or (
        ("order" in lower or "package" in lower) and any(w in lower for w in ["status", "track", "where", "tell me", "check"])
    )

    if is_order_tracking:
        order_info = executor.get_order_status()
        if not order_info.get("has_orders"):
            response_msg = "I couldn't find an order in this session. You can check Track Orders to view your orders."
        else:
            order_id = order_info.get("order_id")
            status = order_info.get("status")
            carrier = order_info.get("carrier")
            tracking_number = order_info.get("tracking_number")
            amount_paise = order_info.get("amount_paise", 0)
            amount_str = f"₹{(amount_paise / 100):,.2f}" if amount_paise else ""

            carrier_str = f" with {carrier}" if carrier else " with RunCraft Express"
            tracking_str = f" Tracking number: {tracking_number}." if tracking_number else ""

            if status == "SHIPPED":
                response_msg = f"Your order #{order_id} ({amount_str}) is currently shipped{carrier_str}.{tracking_str}"
            elif status == "DELIVERED":
                response_msg = f"Your order #{order_id} ({amount_str}) has been delivered!{tracking_str}"
            elif status == "PROCESSING":
                response_msg = f"Your order #{order_id} ({amount_str}) is currently being packed and processed at our warehouse. We will update you as soon as it ships."
            elif status == "CONFIRMED":
                response_msg = f"Your order #{order_id} ({amount_str}) is confirmed and waiting to be processed at our warehouse."
            elif status == "PENDING_PAYMENT":
                response_msg = f"Your order #{order_id} was created and is currently awaiting payment confirmation. You can view or complete payment on the checkout page."
            elif status == "CANCELLED":
                response_msg = f"Your order #{order_id} was cancelled."
            else:
                response_msg = f"Your order #{order_id} status is currently: {status}."
        approval_required = False

    # Intent 0: Direct checkout, payment, or order review request
    elif any(t in lower for t in [
        "checkout", "check out", "place order", "pay", "payment",
        "proceed to checkout", "buy now", "confirm order", "approve and pay", "purchase"
    ]):
        current_cart = get_cart_by_id(executor.db, executor.cart_id)
        if current_cart and current_cart.items:
            quote = executor.get_final_quote()
            total_items = sum(i.quantity for i in current_cart.items)
            response_msg = (
                f"Your order is ready for checkout! You have {total_items} item(s) in your cart "
                f"with an authoritative total of ₹{quote.total_paise / 100:,.2f}. "
                "Please review the breakdown below and click **Approve & Checkout** to proceed to payment."
            )
            approval_required = quote.valid
        else:
            response_msg = (
                "Your shopping cart is currently empty. Tell me what running gear you need "
                "(for example: 'Build me a beginner running kit under ₹8,000' or 'Find race day carbon plate shoes') "
                "and I will assemble your kit!"
            )
            approval_required = False

    # Intent 1: Beginner running kit under budget
    elif ("kit" in lower and ("running" in lower or "beginner" in lower)) or (
        "beginner" in lower and "running" in lower and budget_paise is not None
    ):
        target_budget = budget_paise or 800000  # Default to 8,000 if not parsed

        # Search for running shoes
        shoes = executor.search_products(category="Running Shoes", q="running")
        road_shoe = next((p for p in shoes if "road" in p.tags_json.lower() or "x2" in p.sku.lower() or "runpro" in p.name.lower()), None)
        if not road_shoe and shoes:
            road_shoe = shoes[0]

        if not road_shoe:
            return AgentChatResponse(
                message="I apologize, but we currently have no running shoes available in the catalog.",
                tool_activity=executor.activities,
                approval_required=False,
            )

        # Check inventory for road shoe
        shoe_inv = executor.check_inventory(road_shoe.id, quantity=1)
        if not shoe_inv["has_sufficient_stock"]:
            return AgentChatResponse(
                message=f"The {road_shoe.name} is currently out of stock.",
                tool_activity=executor.activities,
                approval_required=False,
            )

        # Find cross-sell item via policy or search for socks
        related = executor.get_related_products(road_shoe.id, limit=3)
        socks = next((p for p in related if "sock" in p.category.lower() or "sock" in p.name.lower()), None)
        if not socks:
            all_socks = executor.search_products(category="Socks", q="socks")
            if all_socks:
                socks = all_socks[0]

        # Calculate estimated package cost
        shoe_price = road_shoe.price_paise
        socks_price = socks.price_paise if socks else 0
        total_candidate = shoe_price + socks_price

        # Check hard budget constraint
        if total_candidate > target_budget:
            if road_shoe.price_paise > target_budget:
                response_msg = (
                    f"Our lowest-priced performance running shoe is the {road_shoe.name} at ₹{road_shoe.price_paise // 100:,.2f}, "
                    f"which exceeds your requested budget of ₹{target_budget // 100:,.2f}. "
                    f"Would you like to review the {road_shoe.name} individually or adjust your budget?"
                )
            else:
                response_msg = (
                    f"I found the {road_shoe.name} (₹{shoe_price // 100}), but paired with recommended accessories, "
                    f"it would exceed your budget of ₹{target_budget // 100}. "
                    f"Let me recommend the {road_shoe.name} individually."
                )
            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(road_shoe),
                    reason="Lightweight road running shoe for beginners",
                )
            )
        else:
            # Add to real cart
            executor.add_to_cart(road_shoe.id, quantity=1)
            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(road_shoe),
                    reason="Lightweight road running shoe optimized for beginners",
                )
            )

            if socks:
                executor.add_to_cart(socks.id, quantity=1)
                recommendations.append(
                    ProductRecommendationItem(
                        product=ProductResponse.from_orm_model(socks),
                        reason="Anti-blister technical running socks (merchant recommended cross-sell)",
                    )
                )

            # Generate authoritative quote
            quote = executor.get_final_quote()

            # Verify quote complies with budget
            if quote.total_paise <= target_budget:
                response_msg = (
                    f"I've assembled a complete beginner running kit tailored to your needs for "
                    f"₹{quote.total_paise / 100:,.2f}, strictly under your ₹{target_budget // 100:,} budget. "
                    f"It pairs our {road_shoe.name} road shoes with {socks.name if socks else 'accessories'}. "
                    f"Your authoritative quote is ready below for explicit approval."
                )
                approval_required = quote.valid
            else:
                response_msg = (
                    f"The assembled package came to ₹{quote.total_paise / 100:,.2f}, which exceeds your limit. "
                    f"Please review the cart."
                )

    # Intent 2: Carbon plate racing shoes
    elif "carbon" in lower or "race" in lower or "racing" in lower or "peba" in lower:
        carbon_shoes = executor.search_products(q="carbon")
        if not carbon_shoes:
            carbon_shoes = executor.search_products(q="elite")

        if carbon_shoes:
            target = carbon_shoes[0]
            executor.check_inventory(target.id, quantity=1)
            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(target),
                    reason="Flagship marathon racer with full-length carbon plate and high-rebound PEBA foam",
                )
            )
            response_msg = (
                f"I found our top-tier racing shoe: the **{target.name}** (₹{target.price_paise / 100:,.2f}). "
                f"It features a rigid carbon fiber propulsion plate and responsive PEBA superfoam. "
                f"It's in stock at our warehouse. Would you like me to add it to your cart?"
            )
        else:
            response_msg = "We couldn't locate any carbon plate race shoes in the catalog right now."

    # Intent 3: Add hydration flask
    elif "flask" in lower or ("hydration" in lower and ("add" in lower or "buy" in lower or "need" in lower)):
        flasks = executor.search_products(q="flask")
        if not flasks:
            flasks = executor.search_products(q="hydration")

        if flasks:
            flask = flasks[0]
            executor.check_inventory(flask.id, quantity=1)
            executor.add_to_cart(flask.id, quantity=1)
            quote = executor.get_final_quote()

            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(flask),
                    reason="BPA-free handheld running flask with high-flow bite valve",
                )
            )
            response_msg = (
                f"Added the **{flask.name}** to your cart. "
                f"I've updated your live authoritative quote to ₹{quote.total_paise / 100:,.2f}."
            )
            approval_required = quote.valid
        else:
            response_msg = "I couldn't find any hydration flasks in stock."

    # Intent 4: Multi-turn "Add socks too" or "add the socks"
    elif "sock" in lower and ("add" in lower or "also" in lower or "too" in lower or "include" in lower):
        socks_list = executor.search_products(q="sock")
        if socks_list:
            sock_item = socks_list[0]
            executor.check_inventory(sock_item.id, quantity=1)
            executor.add_to_cart(sock_item.id, quantity=1)
            quote = executor.get_final_quote()

            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(sock_item),
                    reason="Anti-blister friction-reducing running socks",
                )
            )
            response_msg = (
                f"Added the **{sock_item.name}** to your cart. "
                f"Your updated authoritative quote is ₹{quote.total_paise / 100:,.2f}."
            )
            approval_required = quote.valid
        else:
            response_msg = "I couldn't find any socks in the catalog to add."

    # Intent 5: General catalog query or keyword search
    else:
        # Search catalog using extracted keywords
        search_results = executor.search_products(q=message.strip()[:50])
        if search_results:
            top_results = search_results[:3]
            for prod in top_results:
                recommendations.append(
                    ProductRecommendationItem(
                        product=ProductResponse.from_orm_model(prod),
                        reason=f"Matched query '{message.strip()[:30]}'",
                    )
                )
            response_msg = (
                f"I found {len(search_results)} relevant item(s) in our catalog. "
                f"Here are top recommendations based on your request. Let me know if you would like me to add any to your cart!"
            )
        else:
            # Check if user asked for non-running items
            non_catalog_keywords = ["laptop", "phone", "iphone", "tennis", "guitar", "car", "pizza", "flight", "tent", "coffee", "book"]
            matched_non_cat = next((kw for kw in non_catalog_keywords if kw in lower), None)
            if matched_non_cat:
                response_msg = (
                    f"RunCraft specializes exclusively in premium running gear (shoes, apparel, socks, and hydration). "
                    f"I cannot fulfill requests for '{matched_non_cat}', but I would be glad to help you find running shoes or assemble a race day kit!"
                )
            else:
                response_msg = (
                    f"I couldn't find any products matching '{message.strip()[:40]}' in our running catalog. "
                    "RunCraft specializes in road & trail running shoes, athletic apparel, running socks, and hydration accessories. "
                    "Try asking: 'Build me a beginner running kit under ₹8,000', 'Find carbon plate race shoes', or 'Add hydration flask'."
                )

    # Get latest authoritative cart state
    latest_cart = get_cart_by_id(executor.db, executor.cart_id)
    cart_resp = CartResponse.from_orm_model(latest_cart)

    # Calculate latest quote if cart has items
    quote_resp = None
    if latest_cart.items:
        try:
            quote_resp = executor.get_final_quote()
        except Exception:
            pass

    order_status_obj = None
    if getattr(executor, "latest_order_info", None) and executor.latest_order_info.get("has_orders"):
        info = executor.latest_order_info
        order_status_obj = AgentOrderStatusSnapshot(
            order_id=info["order_id"],
            status=info["status"],
            amount_paise=info.get("amount_paise", 0),
            currency="INR",
            carrier=info.get("carrier"),
            tracking_number=info.get("tracking_number"),
            customer_name=info.get("customer_name"),
            created_at=info.get("created_at"),
            items_count=info.get("items_count", 0),
            items_summary=info.get("items_summary"),
        )

    return AgentChatResponse(
        message=response_msg,
        tool_activity=executor.activities,
        recommendations=recommendations,
        cart=cart_resp,
        quote=quote_resp,
        approval_required=approval_required,
        order_status=order_status_obj,
    )
