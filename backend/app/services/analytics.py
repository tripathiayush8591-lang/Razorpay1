import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set
from collections import defaultdict

from sqlalchemy import select, func, distinct, or_
from sqlalchemy.orm import Session

from app.models.order import MerchantOrder
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.audit import AuditEvent
from app.services.policy import get_merchant_policy
from app.schemas.analytics import (
    AdminAnalyticsResponse,
    CrossSellPerformanceItem,
    ChannelPerformanceItem,
    DailyTrendItem,
)


CONFIRMED_STATUSES = ("CONFIRMED", "PROCESSING", "SHIPPED", "DELIVERED")


def get_admin_analytics(
    db: Session,
    merchant_id: str,
    days: Optional[int] = None,
) -> AdminAnalyticsResponse:
    """
    Computes authoritative, real-time analytics for the merchant dashboard
    directly from SQLite without mock approximations.
    """
    now = datetime.now(timezone.utc)
    cutoff: Optional[datetime] = None
    if days is not None and days > 0:
        cutoff = now - timedelta(days=days)

    # 1. Topline Financials
    rev_stmt = (
        select(func.coalesce(func.sum(MerchantOrder.amount_paise), 0))
        .where(
            MerchantOrder.merchant_id == merchant_id,
            MerchantOrder.status.in_(CONFIRMED_STATUSES),
        )
    )
    orders_cnt_stmt = (
        select(func.count(MerchantOrder.id))
        .where(
            MerchantOrder.merchant_id == merchant_id,
            MerchantOrder.status.in_(CONFIRMED_STATUSES),
        )
    )
    if cutoff is not None:
        rev_stmt = rev_stmt.where(MerchantOrder.created_at >= cutoff)
        orders_cnt_stmt = orders_cnt_stmt.where(MerchantOrder.created_at >= cutoff)

    gross_revenue_paise: int = db.scalar(rev_stmt) or 0
    confirmed_orders_count: int = db.scalar(orders_cnt_stmt) or 0
    gross_revenue_inr: float = round(gross_revenue_paise / 100.0, 2)

    aov_paise: int = (
        int(gross_revenue_paise / confirmed_orders_count)
        if confirmed_orders_count > 0
        else 0
    )
    aov_inr: float = round(aov_paise / 100.0, 2)

    # Active SKUs in catalog (all-time snapshot of active inventory)
    active_skus_count: int = db.scalar(
        select(func.count(Product.id)).where(
            Product.merchant_id == merchant_id,
            Product.active.is_(True),
        )
    ) or 0

    # 2. Carts & Funnel Metrics
    carts_stmt = select(func.count(Cart.id)).where(Cart.merchant_id == merchant_id)
    carts_with_items_stmt = (
        select(func.count(distinct(CartItem.cart_id)))
        .join(Cart, Cart.id == CartItem.cart_id)
        .where(Cart.merchant_id == merchant_id)
    )
    converted_carts_stmt = select(func.count(Cart.id)).where(
        Cart.merchant_id == merchant_id,
        Cart.status == "converted",
    )

    if cutoff is not None:
        carts_stmt = carts_stmt.where(Cart.created_at >= cutoff)
        carts_with_items_stmt = carts_with_items_stmt.where(Cart.created_at >= cutoff)
        converted_carts_stmt = converted_carts_stmt.where(Cart.created_at >= cutoff)

    total_carts_created: int = db.scalar(carts_stmt) or 0
    carts_with_items_count: int = db.scalar(carts_with_items_stmt) or 0
    converted_carts_count: int = db.scalar(converted_carts_stmt) or 0
    abandoned_carts_count: int = max(0, carts_with_items_count - converted_carts_count)

    cart_to_order_conversion_rate: float = (
        round((confirmed_orders_count / carts_with_items_count) * 100.0, 1)
        if carts_with_items_count > 0
        else 0.0
    )
    overall_conversion_rate: float = (
        round((confirmed_orders_count / total_carts_created) * 100.0, 1)
        if total_carts_created > 0
        else 0.0
    )

    # 3. AI Conversations & Telemetry
    # In-app agent turns and sessions
    in_app_turns_stmt = select(func.count(AuditEvent.id)).where(
        AuditEvent.merchant_id == merchant_id,
        AuditEvent.actor_type == "agent",
        AuditEvent.action == "agent_chat_turn",
    )
    in_app_sess_stmt = select(func.count(distinct(AuditEvent.session_id))).where(
        AuditEvent.merchant_id == merchant_id,
        AuditEvent.actor_type == "agent",
        AuditEvent.action == "agent_chat_turn",
    )

    # External AI buyer tool executions and sessions via MCP
    ext_tools_stmt = select(func.count(AuditEvent.id)).where(
        or_(AuditEvent.merchant_id == merchant_id, AuditEvent.merchant_id.is_(None)),
        AuditEvent.actor_type == "external_ai_buyer",
    )
    ext_sess_stmt = select(func.count(distinct(AuditEvent.session_id))).where(
        or_(AuditEvent.merchant_id == merchant_id, AuditEvent.merchant_id.is_(None)),
        AuditEvent.actor_type == "external_ai_buyer",
    )

    if cutoff is not None:
        in_app_turns_stmt = in_app_turns_stmt.where(AuditEvent.created_at >= cutoff)
        in_app_sess_stmt = in_app_sess_stmt.where(AuditEvent.created_at >= cutoff)
        ext_tools_stmt = ext_tools_stmt.where(AuditEvent.created_at >= cutoff)
        ext_sess_stmt = ext_sess_stmt.where(AuditEvent.created_at >= cutoff)

    in_app_agent_turns_count: int = db.scalar(in_app_turns_stmt) or 0
    in_app_agent_sessions_count: int = db.scalar(in_app_sess_stmt) or 0
    external_ai_tool_calls_count: int = db.scalar(ext_tools_stmt) or 0
    external_ai_sessions_count: int = db.scalar(ext_sess_stmt) or 0

    # Distinct combined AI sessions
    ai_sess_union_stmt = select(distinct(AuditEvent.session_id)).where(
        or_(AuditEvent.merchant_id == merchant_id, AuditEvent.merchant_id.is_(None)),
        AuditEvent.actor_type.in_(["agent", "external_ai_buyer"]),
    )
    if cutoff is not None:
        ai_sess_union_stmt = ai_sess_union_stmt.where(AuditEvent.created_at >= cutoff)
    ai_sessions_rows = db.scalars(ai_sess_union_stmt).all()
    total_ai_sessions_count: int = len({s for s in ai_sessions_rows if s})

    # 4. Fetch confirmed orders for cross-sell and channel attribution
    orders_query = (
        select(MerchantOrder)
        .where(
            MerchantOrder.merchant_id == merchant_id,
            MerchantOrder.status.in_(CONFIRMED_STATUSES),
        )
    )
    if cutoff is not None:
        orders_query = orders_query.where(MerchantOrder.created_at >= cutoff)

    confirmed_orders = list(db.scalars(orders_query).all())

    # 5. Cross-Sell Acceptance Analysis
    policy = get_merchant_policy(db, merchant_id)
    raw_rules = []
    try:
        raw_rules = json.loads(policy.cross_sell_rules_json or "[]")
    except Exception:
        raw_rules = []

    # Map of rule triggers and recommendations:
    # [{"trigger_category": "footwear", "recommend_category": "socks"}]
    parsed_rules = []
    for r in raw_rules:
        trig = r.get("trigger_category", "").strip().lower()
        rec = r.get("recommend_category", "").strip().lower()
        if trig and rec:
            parsed_rules.append((trig, rec, r.get("trigger_category"), r.get("recommend_category")))

    # Product category map for fast lookups
    all_products = db.execute(
        select(Product.id, Product.category).where(Product.merchant_id == merchant_id)
    ).all()
    prod_cat_map: Dict[str, str] = {row[0]: (row[1] or "").strip().lower() for row in all_products}

    rule_match_counts = defaultdict(int)
    cross_sell_eligible_orders_count = 0
    cross_sell_accepted_orders_count = 0

    for ord_obj in confirmed_orders:
        item_categories: Set[str] = set()
        try:
            items_raw = json.loads(ord_obj.items_snapshot_json or "[]")
            for itm in items_raw:
                p_id = itm.get("product_id")
                if p_id and p_id in prod_cat_map:
                    item_categories.add(prod_cat_map[p_id])
                elif "category" in itm and itm["category"]:
                    item_categories.add(itm["category"].strip().lower())
        except Exception:
            continue

        if not item_categories:
            continue

        # Check if order was eligible (contains any trigger category)
        is_eligible = any(trig in item_categories for trig, _, _, _ in parsed_rules)
        if is_eligible:
            cross_sell_eligible_orders_count += 1

        # Check if order accepted any cross-sell rule (contains both trigger and recommend)
        order_accepted = False
        for trig, rec, orig_trig, orig_rec in parsed_rules:
            if trig in item_categories and rec in item_categories:
                rule_match_counts[(orig_trig, orig_rec)] += 1
                order_accepted = True

        if order_accepted:
            cross_sell_accepted_orders_count += 1

    cross_sell_acceptance_rate = (
        round((cross_sell_accepted_orders_count / cross_sell_eligible_orders_count) * 100.0, 1)
        if cross_sell_eligible_orders_count > 0
        else 0.0
    )

    cross_sell_rules_summary = [
        CrossSellPerformanceItem(
            trigger_category=trig_name,
            recommend_category=rec_name,
            matches_count=rule_match_counts.get((trig_name, rec_name), 0),
        )
        for _, _, trig_name, rec_name in parsed_rules
    ]

    # 6. Channel Attribution Breakdown
    # Retrieve sessions associated with AI activity from audit_events
    agent_sessions_stmt = select(distinct(AuditEvent.session_id)).where(
        AuditEvent.actor_type == "agent",
    )
    ext_sessions_stmt = select(distinct(AuditEvent.session_id)).where(
        AuditEvent.actor_type == "external_ai_buyer",
    )
    agent_sessions: Set[str] = {s for s in db.scalars(agent_sessions_stmt).all() if s}
    ext_sessions: Set[str] = {s for s in db.scalars(ext_sessions_stmt).all() if s}

    # Fetch Cart session IDs for all confirmed orders
    cart_ids = [o.cart_id for o in confirmed_orders if o.cart_id]
    cart_session_map: Dict[str, str] = {}
    if cart_ids:
        cart_rows = db.scalars(select(Cart).where(Cart.id.in_(cart_ids))).all()
        cart_session_map = {c.id: c.session_id for c in cart_rows}

    channel_orders = defaultdict(int)
    channel_revenue = defaultdict(int)

    for ord_obj in confirmed_orders:
        c_sess = cart_session_map.get(ord_obj.cart_id, "") if ord_obj.cart_id else ""
        
        # Attribution precedence:
        # 1. External AI Buyer: session in ext_sessions or session starts with ext_buyer_
        # 2. In-App AI Agent: session in agent_sessions
        # 3. Direct Storefront: all others
        if c_sess and (c_sess in ext_sessions or c_sess.startswith("ext_buyer_")):
            ch = "external_ai"
        elif c_sess and (c_sess in agent_sessions):
            ch = "in_app_agent"
        else:
            ch = "direct_storefront"

        channel_orders[ch] += 1
        channel_revenue[ch] += ord_obj.amount_paise

    channel_labels = {
        "direct_storefront": "Direct Storefront",
        "in_app_agent": "In-App AI Agent",
        "external_ai": "External AI Buyer (MCP)",
    }

    channel_breakdown: List[ChannelPerformanceItem] = []
    for ch_key, ch_name in channel_labels.items():
        o_count = channel_orders[ch_key]
        r_paise = channel_revenue[ch_key]
        r_inr = round(r_paise / 100.0, 2)
        share = (
            round((r_paise / gross_revenue_paise) * 100.0, 1)
            if gross_revenue_paise > 0
            else 0.0
        )
        channel_breakdown.append(
            ChannelPerformanceItem(
                channel=ch_key,
                channel_label=ch_name,
                orders_count=o_count,
                revenue_paise=r_paise,
                revenue_inr=r_inr,
                share_percentage=share,
            )
        )

    # 7. Daily Trends (last 14 days or days in window)
    trend_days = min(days if (days and days > 0) else 14, 30)
    start_date = (now - timedelta(days=trend_days - 1)).date()
    start_datetime = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    daily_order_counts = defaultdict(int)
    daily_revenues = defaultdict(int)

    for ord_obj in confirmed_orders:
        if ord_obj.created_at:
            ord_date = ord_obj.created_at.date()
            if ord_date >= start_date:
                daily_order_counts[ord_date] += 1
                daily_revenues[ord_date] += ord_obj.amount_paise

    # Aggregate actual daily distinct AI sessions from audit_events
    daily_ai_sessions = defaultdict(set)
    audit_events_stmt = select(AuditEvent.created_at, AuditEvent.session_id).where(
        or_(AuditEvent.merchant_id == merchant_id, AuditEvent.merchant_id.is_(None)),
        AuditEvent.actor_type.in_(["agent", "external_ai_buyer"]),
        AuditEvent.created_at >= start_datetime,
    )
    for created_at_val, sess_id in db.execute(audit_events_stmt).all():
        if created_at_val and sess_id:
            daily_ai_sessions[created_at_val.date()].add(sess_id)

    daily_trends: List[DailyTrendItem] = []
    for d_offset in range(trend_days):
        current_date = start_date + timedelta(days=d_offset)
        rev_paise = daily_revenues[current_date]
        daily_trends.append(
            DailyTrendItem(
                date=current_date.isoformat(),
                orders_count=daily_order_counts[current_date],
                revenue_inr=round(rev_paise / 100.0, 2),
                ai_sessions_count=len(daily_ai_sessions[current_date]),
            )
        )

    return AdminAnalyticsResponse(
        gross_revenue_paise=gross_revenue_paise,
        gross_revenue_inr=gross_revenue_inr,
        confirmed_orders_count=confirmed_orders_count,
        active_skus_count=active_skus_count,
        aov_paise=aov_paise,
        aov_inr=aov_inr,
        total_carts_created=total_carts_created,
        carts_with_items_count=carts_with_items_count,
        converted_carts_count=converted_carts_count,
        abandoned_carts_count=abandoned_carts_count,
        cart_to_order_conversion_rate=cart_to_order_conversion_rate,
        overall_conversion_rate=overall_conversion_rate,
        in_app_agent_turns_count=in_app_agent_turns_count,
        in_app_agent_sessions_count=in_app_agent_sessions_count,
        external_ai_tool_calls_count=external_ai_tool_calls_count,
        external_ai_sessions_count=external_ai_sessions_count,
        total_ai_sessions_count=total_ai_sessions_count,
        cross_sell_eligible_orders_count=cross_sell_eligible_orders_count,
        cross_sell_accepted_orders_count=cross_sell_accepted_orders_count,
        cross_sell_acceptance_rate=cross_sell_acceptance_rate,
        cross_sell_rules_summary=cross_sell_rules_summary,
        channel_breakdown=channel_breakdown,
        daily_trends=daily_trends,
        days_window=days,
    )
