import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.db.seed import seed_database, CANONICAL_PRODUCTS, DEMO_MERCHANT_ID
from app.models.merchant import Merchant
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.models.policy import MerchantPolicy
from app.models.order import MerchantOrder
from app.models.cart import Cart
from app.services.analytics import get_admin_analytics

client = TestClient(app)


def test_seed_database_idempotent():
    """Verify seed_database can run multiple times without error or duplicating canonical records."""
    with SessionLocal() as db:
        # Run seed once
        seed_database(db, reset=False)
        count_1 = db.query(Product).count()
        orders_1 = db.query(MerchantOrder).count()

        # Run seed again (idempotent)
        seed_database(db, reset=False)
        count_2 = db.query(Product).count()
        orders_2 = db.query(MerchantOrder).count()

        assert count_1 == count_2 == len(CANONICAL_PRODUCTS)
        assert orders_1 == orders_2


def test_seed_admin_credentials():
    """Verify demo admin account can log in with configured password and get signed JWT/session."""
    with SessionLocal() as db:
        seed_database(db, reset=False)

    res = client.post(
        "/api/admin/login",
        json={"email": settings.ADMIN_EMAIL, "password": settings.ADMIN_PASSWORD},
    )
    assert res.status_code == 200
    data = res.json()["data"]
    assert "token" in data
    assert data["admin"]["email"] == settings.ADMIN_EMAIL
    assert data["admin"]["role"] == "admin"


def test_seed_canonical_products():
    """Verify all 10 canonical products are seeded with required fields, stock, and active status."""
    with SessionLocal() as db:
        seed_database(db, reset=False)
        products = db.query(Product).filter(Product.active.is_(True)).all()
        assert len(products) == len(CANONICAL_PRODUCTS)

        sku_map = {p.sku: p for p in products}
        for item in CANONICAL_PRODUCTS:
            assert item["sku"] in sku_map
            db_p = sku_map[item["sku"]]
            assert db_p.price_paise == item["price_paise"]
            assert db_p.inventory_quantity >= 20
            assert db_p.category == item["category"]
            assert db_p.name == item["name"]


def test_seed_policies():
    """Verify merchant policy is created with configured rules."""
    with SessionLocal() as db:
        seed_database(db, reset=False)
        policy = db.query(MerchantPolicy).first()
        assert policy is not None
        assert policy.require_purchase_approval is True
        assert policy.allow_out_of_stock is False
        assert policy.max_discount_percent == 15
        assert "Running Shoes" in policy.cross_sell_rules_json
        assert "free_delivery_threshold_paise" in policy.delivery_rules_json


def test_seed_baseline_orders_and_fulfillment_ready():
    """Verify baseline demo orders exist across channels and at least one is in CONFIRMED state for fulfillment demo."""
    with SessionLocal() as db:
        seed_database(db, reset=False)
        orders = db.query(MerchantOrder).all()
        assert len(orders) >= 5

        statuses = {o.status for o in orders}
        assert "CONFIRMED" in statuses, "Must have a CONFIRMED order ready for live fulfillment demo"
        assert "PROCESSING" in statuses
        assert "SHIPPED" in statuses
        assert "DELIVERED" in statuses

        confirmed_order = next(o for o in orders if o.status == "CONFIRMED")
        assert confirmed_order.customer_name == "Arjun Sharma"
        assert confirmed_order.amount_paise > 0
        assert confirmed_order.cart_id is not None


def test_seed_analytics_populated():
    """Verify analytics service returns complete, non-zero metrics immediately from seed baseline."""
    with SessionLocal() as db:
        seed_database(db, reset=False)
        merchant = db.query(Merchant).first()
        assert merchant is not None
        analytics = get_admin_analytics(db, merchant.id)

        assert analytics.confirmed_orders_count >= 5
        assert analytics.gross_revenue_inr > 0
        assert analytics.aov_inr > 0
        assert analytics.active_skus_count == len(CANONICAL_PRODUCTS)
        assert analytics.cart_to_order_conversion_rate > 0

        # Channel breakdown verification
        channel_names = {c.channel for c in analytics.channel_breakdown}
        assert "direct_storefront" in channel_names
        assert "in_app_agent" in channel_names
        assert "external_ai" in channel_names

        # Cross-sell rules verification
        shoes_rule = next(
            (r for r in analytics.cross_sell_rules_summary if "Shoe" in r.trigger_category),
            None,
        )
        assert shoes_rule is not None
        assert shoes_rule.matches_count >= 1
