import logging
from typing import Any, Dict, List, Optional
from google import genai
from google.genai import types

from app.core.config import settings
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

logger = logging.getLogger(__name__)

SYSTEM_INSTRUCTION = """
You are the RunCraft AI Commerce Assistant for an athletic footwear and apparel merchant.
Your mission is to help shoppers find products, check live inventory, assemble gear kits, and prepare authoritative quotes.

CRITICAL RULES:
1. You must NEVER fabricate or hallucinate prices, inventory quantities, delivery fees, or discounts.
2. All product details, stock levels, and quotes MUST come directly from tool responses.
3. User budget constraints are HARD upper limits. Never exceed the user's budget.
4. Stop before payment: when a package or cart is ready for purchase, inform the user that their authoritative quote is ready for their explicit approval.
5. Keep your tone professional, concise, and helpful.
"""


def is_gemini_available() -> bool:
    """Check whether a real Gemini API key is configured."""
    key = settings.GEMINI_API_KEY.strip()
    return bool(key and not key.startswith("your_") and not key.startswith("sk-") and key != "placeholder")


def run_gemini_turn(
    executor: AgentToolExecutor,
    message: str,
    history: Optional[List[ChatMessageTurn]] = None,
) -> AgentChatResponse:
    """
    Run an agent turn using Google Gemini API with function calling.
    Delegates all tool calls to AgentToolExecutor.
    """
    if not is_gemini_available():
        raise RuntimeError("GEMINI_API_KEY is not configured or is a placeholder")

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    # Tool definitions mapping to executor
    def search_products(q: str = "", category: str = "", max_price_inr: int = 0) -> List[Dict[str, Any]]:
        """Search products in the catalog by query, category, or maximum price in INR."""
        max_paise = max_price_inr * 100 if max_price_inr > 0 else None
        results = executor.search_products(q=q or None, category=category or None, max_price_paise=max_paise)
        return [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "price_inr": p.price_paise / 100,
                "inventory_quantity": p.inventory_quantity,
                "short_description": p.short_description,
            }
            for p in results
        ]

    def check_inventory(product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Check live physical stock for a product."""
        return executor.check_inventory(product_id=product_id, quantity=quantity)

    def get_related_products(product_id: str) -> List[Dict[str, Any]]:
        """Find related or cross-sell products based on merchant policies."""
        related = executor.get_related_products(product_id=product_id)
        return [
            {
                "id": p.id,
                "sku": p.sku,
                "name": p.name,
                "category": p.category,
                "price_inr": p.price_paise / 100,
                "inventory_quantity": p.inventory_quantity,
            }
            for p in related
        ]

    def add_to_cart(product_id: str, quantity: int = 1) -> Dict[str, Any]:
        """Add a product to the user's active shopping cart."""
        updated_cart = executor.add_to_cart(product_id=product_id, quantity=quantity)
        return {
            "success": True,
            "cart_id": updated_cart.id,
            "total_items": len(updated_cart.items),
        }

    def remove_from_cart(item_id: str) -> Dict[str, Any]:
        """Remove a product from the user's active shopping cart."""
        updated_cart = executor.remove_from_cart(item_id=item_id)
        return {
            "success": True,
            "cart_id": updated_cart.id,
            "total_items": len(updated_cart.items),
        }

    def get_final_quote() -> Dict[str, Any]:
        """Calculate authoritative price, discounts, delivery fee, and total."""
        quote = executor.get_final_quote()
        return {
            "subtotal_inr": quote.subtotal_paise / 100,
            "discount_inr": quote.discount_paise / 100,
            "delivery_inr": quote.delivery_paise / 100,
            "total_inr": quote.total_paise / 100,
            "valid": quote.valid,
            "warnings": quote.warnings,
        }

    tool_dispatch = {
        "search_products": search_products,
        "check_inventory": check_inventory,
        "get_related_products": get_related_products,
        "add_to_cart": add_to_cart,
        "remove_from_cart": remove_from_cart,
        "get_final_quote": get_final_quote,
    }

    tools_list = [
        search_products,
        check_inventory,
        get_related_products,
        add_to_cart,
        remove_from_cart,
        get_final_quote,
    ]

    # Assemble conversation contents for the Gemini SDK
    contents: List[Any] = []
    if history:
        for turn in history[-4:]:
            role = "user" if turn.role == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=turn.content)]))

    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=message)]))

    # Run tool execution loop (up to 5 iterations)
    max_turns = 5
    final_text = ""
    recommended_product_ids = set()

    for _ in range(max_turns):
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=tools_list,
            temperature=0.2,
        )

        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=contents,
            config=config,
        )

        # Check for function calls
        function_calls = response.function_calls
        if not function_calls:
            final_text = response.text or ""
            break

        # Append model response to conversation contents
        contents.append(response.candidates[0].content)

        # Execute each function call and append response parts
        response_parts = []
        for call in function_calls:
            func = tool_dispatch.get(call.name)
            args = dict(call.args) if call.args else {}

            if "product_id" in args:
                recommended_product_ids.add(args["product_id"])

            try:
                result = func(**args) if func else {"error": f"Unknown function {call.name}"}
            except Exception as ex:
                result = {"error": str(ex)}

            response_parts.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": result},
                )
            )

        contents.append(types.Content(role="user", parts=response_parts))

    # Fetch latest authoritative cart
    latest_cart = get_cart_by_id(executor.db, executor.cart_id)
    cart_resp = CartResponse.from_orm_model(latest_cart)

    # Fetch latest authoritative quote if cart has items
    quote_resp = None
    approval_required = False
    if latest_cart.items:
        try:
            quote_resp = executor.get_final_quote()
            approval_required = quote_resp.valid
        except Exception:
            pass

    # Compile recommendations from any touched products
    recommendations: List[ProductRecommendationItem] = []
    for pid in recommended_product_ids:
        try:
            p = executor.get_product(pid)
            recommendations.append(
                ProductRecommendationItem(
                    product=ProductResponse.from_orm_model(p),
                    reason="Selected by AI assistant based on query constraints",
                )
            )
        except Exception:
            pass

    return AgentChatResponse(
        message=final_text or "Here are my recommendations based on your request.",
        tool_activity=executor.activities,
        recommendations=recommendations,
        cart=cart_resp,
        quote=quote_resp,
        approval_required=approval_required,
    )
