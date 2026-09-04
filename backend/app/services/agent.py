import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.schemas.agent import AgentChatResponse, ChatMessageTurn
from app.services.cart import get_or_create_cart, get_cart_by_id, verify_cart_ownership
from app.services.agent_tools import AgentToolExecutor
from app.services.agent_fallback import run_deterministic_fallback
from app.services.audit import log_audit_event
from app.integrations.gemini import is_gemini_available, run_gemini_turn

logger = logging.getLogger(__name__)


def process_agent_chat(
    db: Session,
    session_id: str,
    message: str,
    cart_id: Optional[str] = None,
    history: Optional[List[ChatMessageTurn]] = None,
) -> AgentChatResponse:
    """
    Central orchestration service for In-App AI Agent.
    Binds to authoritative guest session and cart.
    Routes between Gemini (if configured and working) and deterministic fallback.
    Records audit trail and returns structured response.
    """
    clean_session_id = session_id.strip()

    # Authoritative cart binding
    if cart_id:
        cart = get_cart_by_id(db, cart_id=cart_id, session_id=clean_session_id)
    else:
        cart = get_or_create_cart(db, session_id=clean_session_id)

    # Initialize tool execution engine with session and cart context
    executor = AgentToolExecutor(db=db, session_id=clean_session_id, cart_id=cart.id)

    provider_used = "fallback"
    response: Optional[AgentChatResponse] = None

    # Try Gemini if API key is present
    if is_gemini_available():
        try:
            logger.info("Attempting agent turn with Google Gemini API")
            response = run_gemini_turn(executor=executor, message=message, history=history)
            provider_used = "gemini"
        except Exception as e:
            logger.warning(f"Gemini agent call failed ({e}), switching to deterministic fallback")
            # Clear partially recorded activities so fallback provides a clean, coherent activity stream
            executor.activities.clear()
            response = None

    # Fallback path if Gemini unavailable or failed
    if response is None:
        logger.info("Running deterministic fallback orchestrator")
        response = run_deterministic_fallback(executor=executor, message=message, history=history)
        provider_used = "fallback"

    # Ensure order status is authoritatively attached if queried or tool was invoked
    order_status_triggers = [
        "order status", "status of my order", "where is my order", "where's my order",
        "track my order", "track order", "track my package", "track package", "where is my package",
        "tell me my order status", "tell me the status of my order", "show my order",
        "my order status", "check my order", "order tracking", "order update", "check order"
    ]
    is_order_status_query = any(t in message.lower() for t in order_status_triggers) or (
        ("order" in message.lower() or "package" in message.lower()) and any(w in message.lower() for w in ["status", "track", "where", "tell me", "check"])
    )

    if is_order_status_query and response and not response.order_status:
        info = executor.get_order_status()
        if info.get("has_orders"):
            from app.schemas.agent import AgentOrderStatusSnapshot
            response.order_status = AgentOrderStatusSnapshot(
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
            if "order #" not in response.message.lower() and "status:" not in response.message.lower() and "status is" not in response.message.lower():
                amount_str = f"₹{(info.get('amount_paise', 0) / 100):,.2f}"
                response.message += f"\n\nHere is your latest order #{info['order_id']} ({amount_str}): Status is **{info['status']}**."
    elif response and not response.order_status and getattr(executor, "latest_order_info", None) and executor.latest_order_info.get("has_orders"):
        from app.schemas.agent import AgentOrderStatusSnapshot
        info = executor.latest_order_info
        response.order_status = AgentOrderStatusSnapshot(
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

    # Record authoritative audit event for this agent turn
    try:
        quote_total = response.quote.total_paise if response.quote else 0
        tool_names = [a.activity for a in response.tool_activity]
        log_audit_event(
            db=db,
            actor_type="agent",
            action="agent_chat_turn",
            entity_type="cart",
            entity_id=cart.id,
            session_id=clean_session_id,
            merchant_id=cart.merchant_id,
            metadata={
                "provider": provider_used,
                "user_prompt": message[:200],
                "tool_calls_count": len(response.tool_activity),
                "tools_executed": tool_names,
                "quote_total_paise": quote_total,
                "approval_required": response.approval_required,
            },
        )
    except Exception as audit_err:
        logger.warning(f"Failed to log audit event for agent turn: {audit_err}")

    return response
