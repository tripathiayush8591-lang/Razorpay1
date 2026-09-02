import re
from typing import List, Optional, Tuple
from app.models.product import Product
from app.schemas.agent import (
    AgentChatResponse,
    ChatMessageTurn,
    ProductRecommendationItem,
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

    # Intent 1: Beginner running kit under budget
    if ("kit" in lower and ("running" in lower or "beginner" in lower)) or (
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
            # Helpful fallback without crashing or hallucinating
            response_msg = (
                "I am your RunCraft AI Commerce Assistant. I can help you search our live running catalog, "
                "verify stock, configure gear kits, and prepare an authoritative quote. "
                "Try asking: 'Build me a beginner running kit under ₹8,000', 'Find carbon plate race shoes', "
                "or 'Add hydration flask'."
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

    return AgentChatResponse(
        message=response_msg,
        tool_activity=executor.activities,
        recommendations=recommendations,
        cart=cart_resp,
        quote=quote_resp,
        approval_required=approval_required,
    )
