import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select, delete

from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.core.config import settings
from app.core.security import hash_password
from app.models.merchant import Merchant
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.models.policy import MerchantPolicy
from app.models.cart import Cart, CartItem
from app.models.order import MerchantOrder
from app.models.payment import PaymentAttempt
from app.models.audit import AuditEvent
from app.models.webhook_event import ProcessedWebhookEvent


DEMO_MERCHANT_ID = "merch_runcraft_demo"
DEMO_ADMIN_ID = "admin_runcraft_demo"
DEMO_POLICY_ID = "pol_runcraft_demo"

# 10 Canonical RunCraft Products
CANONICAL_PRODUCTS = [
    {
        "id": "prod_runpro_x2",
        "sku": "RUN-X2-BLK-42",
        "name": "RunPro X2 Road Runner",
        "category": "Running Shoes",
        "short_description": "Lightweight, responsive road running shoes built for beginner to intermediate runners.",
        "description": "Engineered with dual-density foam for plush shock absorption and high energy return. Breathable jacquard mesh upper keeps feet cool during long morning runs.",
        "price_paise": 549900,  # ₹5,499.00
        "inventory_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&auto=format&fit=crop&q=60",
        "tags": ["running", "shoes", "beginner", "road", "lightweight"],
        "attributes": {"color": "Midnight Black", "size": "42 EU", "drop_mm": 8, "weight_grams": 240},
        "active": True,
    },
    {
        "id": "prod_swiftstride",
        "sku": "SWIFT-STRIDE-BLU-41",
        "name": "SwiftStride Daily Trainer",
        "category": "Running Shoes",
        "short_description": "Budget-friendly, high-cushion everyday trainer ideal for couch-to-5K athletes.",
        "description": "A durable all-around training shoe offering wide base stability, padded tongue and collar, and high-traction rubber outsole designed for Indian road conditions.",
        "price_paise": 399900,  # ₹3,999.00
        "inventory_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1595950653106-6c9ebd614d3a?w=800&auto=format&fit=crop&q=60",
        "tags": ["running", "shoes", "beginner", "daily trainer", "budget"],
        "attributes": {"color": "Ocean Blue", "size": "41 EU", "drop_mm": 10, "weight_grams": 275},
        "active": True,
    },
    {
        "id": "prod_carbon_race",
        "sku": "CARB-RACE-NEON-42",
        "name": "Carbon Race Elite 3",
        "category": "Running Shoes",
        "short_description": "Full-length carbon fiber plated race day shoe for competitive marathon runners.",
        "description": "Ultralight supercritical PEBA foam combined with an aggressive spoon-shaped carbon plate. Delivers maximum propulsion and fatigue reduction over race distances.",
        "price_paise": 1499900,  # ₹14,999.00
        "inventory_quantity": 20,
        "image_url": "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2?w=800&auto=format&fit=crop&q=60",
        "tags": ["running", "shoes", "marathon", "carbon-plate", "elite"],
        "attributes": {"color": "Volt Neon", "size": "42 EU", "drop_mm": 4, "weight_grams": 195},
        "active": True,
    },
    {
        "id": "prod_aerovent_singlet",
        "sku": "APP-AERO-SGLT-M",
        "name": "AeroVent Seamless Running Singlet",
        "category": "Running Apparel",
        "short_description": "Ultra-breathable moisture-wicking technical running singlet with anti-chafing bonded seams.",
        "description": "Crafted from micro-perforated polyester with quick-dry technology and odor-resistant silver ion treatment. Reflective detailing on chest and back.",
        "price_paise": 149900,  # ₹1,499.00
        "inventory_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1581655353564-df123a1eb820?w=800&auto=format&fit=crop&q=60",
        "tags": ["apparel", "singlet", "moisture-wicking", "summer", "running"],
        "attributes": {"color": "Charcoal Grey", "size": "M", "fit": "Athletic Slim"},
        "active": True,
    },
    {
        "id": "prod_paceshorts_5",
        "sku": "APP-PACE-SHRT-M",
        "name": "PaceShorts 5\" 2-in-1",
        "category": "Running Apparel",
        "short_description": "5-inch inseam lightweight running shorts with built-in compressive liner and bounce-free phone pocket.",
        "description": "Water-resistant 4-way stretch outer shell with an internal compressive liner to prevent chafing. Features zippered back key pocket and side stash pocket.",
        "price_paise": 189900,  # ₹1,899.00
        "inventory_quantity": 50,
        "image_url": "https://images.unsplash.com/photo-1591195853828-11db59a44f6b?w=800&auto=format&fit=crop&q=60",
        "tags": ["apparel", "shorts", "2-in-1", "phone-pocket", "running"],
        "attributes": {"color": "Matte Black", "size": "M", "inseam_inches": 5},
        "active": True,
    },
    {
        "id": "prod_fleet_socks",
        "sku": "ACC-FLT-SCK-3PK",
        "name": "FleetStride Anti-Blister Socks (3-Pack)",
        "category": "Running Socks",
        "short_description": "Seamless toe, anatomical arch support socks engineered specifically for endurance runners.",
        "description": "Double-cuff ankle design prevents slippage. High-density padding under heel and metatarsal pads guards against hot spots and friction blisters.",
        "price_paise": 69900,  # ₹699.00
        "inventory_quantity": 100,
        "image_url": "https://images.unsplash.com/photo-1586350977771-b3b0abd50c82?w=800&auto=format&fit=crop&q=60",
        "tags": ["socks", "anti-blister", "accessories", "cushion", "3-pack"],
        "attributes": {"color": "White / Grey", "size": "One Size (EU 39-44)", "pack_count": 3},
        "active": True,
    },
    {
        "id": "prod_flask_500",
        "sku": "HYD-FLSK-500ML",
        "name": "HydroGrip 500ml Handheld Flask",
        "category": "Hydration & Accessories",
        "short_description": "Ergonomic handheld soft flask with adjustable hand strap and bite valve.",
        "description": "Collapses as you drink to minimize water sloshing. BPA/PVC-free TPU construction. Includes zipper pouch for energy gels or car key.",
        "price_paise": 89900,  # ₹899.00
        "inventory_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1523362628745-0c100150b504?w=800&auto=format&fit=crop&q=60",
        "tags": ["hydration", "flask", "running", "accessories", "soft-bottle"],
        "attributes": {"capacity_ml": 500, "material": "BPA-free TPU", "weight_empty_grams": 48},
        "active": True,
    },
    {
        "id": "prod_running_cap",
        "sku": "ACC-VENT-CAP-WHT",
        "name": "SolarBreeze Laser-Vent Running Cap",
        "category": "Hydration & Accessories",
        "short_description": "UPF 50+ sun protection cap with laser-perforated side panels and dark underbill.",
        "description": "Ultralight sweat-wicking headwear with glare-reducing black underbill and reflective hook-and-loop rear closure.",
        "price_paise": 79900,  # ₹799.00
        "inventory_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1588850561407-ed78c282e89b?w=800&auto=format&fit=crop&q=60",
        "tags": ["cap", "accessories", "sun-protection", "lightweight", "running"],
        "attributes": {"color": "Arctic White", "uv_rating": "UPF 50+", "weight_grams": 42},
        "active": True,
    },
    {
        "id": "prod_electrolyte_tabs",
        "sku": "NUT-ELEC-CITRUS-20",
        "name": "Electrolyte Endurance Tablets (20 Effervescent Tabs)",
        "category": "Nutrition & Recovery",
        "short_description": "Fast-dissolving effervescent hydration tablets rich in sodium, potassium, and magnesium.",
        "description": "Zero sugar, light citrus taste formulated for tropical climate training to prevent cramping and maintain fluid balance.",
        "price_paise": 49900,  # ₹499.00
        "inventory_quantity": 100,
        "image_url": "https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=800&auto=format&fit=crop&q=60",
        "tags": ["nutrition", "electrolytes", "hydration", "recovery", "cramp-prevention"],
        "attributes": {"flavor": "Lemon Lime", "servings": 20, "sugar_grams": 0},
        "active": True,
    },
    {
        "id": "prod_massage_roller",
        "sku": "REC-MASSAGE-BALL",
        "name": "Deep Tissue Lacrosse Massage Ball",
        "category": "Nutrition & Recovery",
        "short_description": "High-density trigger point therapy massage ball for plantar fasciitis and hamstring recovery.",
        "description": "Solid natural rubber construction provides targeted pressure to release myofascial knots in feet, glutes, and shoulders after hard running workouts.",
        "price_paise": 34900,  # ₹349.00
        "inventory_quantity": 60,
        "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&auto=format&fit=crop&q=60",
        "tags": ["recovery", "massage", "accessories", "plantar-fasciitis"],
        "attributes": {"diameter_mm": 63, "material": "High Density Natural Rubber"},
        "active": True,
    },
]


def seed_database(db: Session, reset: bool = False, catalog_only: bool = False) -> None:
    """
    Seeds the database deterministically.
    
    - reset=True: Performs a clean demo wipe of transactional data (orders, carts, audit events)
                  and restores the exact pristine demo catalog, merchant, policies, and baseline demo orders.
    - catalog_only=True: Restores catalog, merchant, and policies without baseline orders.
    - default (reset=False): Idempotently updates merchant, admin, policies, and catalog.
    """
    Base.metadata.create_all(bind=engine)
    now = datetime.now(timezone.utc)

    # 1. Reset transactional tables if requested
    if reset:
        print("[Demo Seed] Performing clean demo reset...")
        db.query(PaymentAttempt).delete()
        db.query(MerchantOrder).delete()
        db.query(CartItem).delete()
        db.query(Cart).delete()
        db.query(AuditEvent).delete()
        db.query(ProcessedWebhookEvent).delete()
        db.query(Product).delete()
        db.query(MerchantPolicy).delete()
        db.commit()

    # 2. Seed / Upsert Merchant
    merchant = db.query(Merchant).filter(Merchant.slug == "runcraft").first()
    if not merchant:
        merchant = Merchant(
            id=DEMO_MERCHANT_ID,
            name="RunCraft Athletics",
            slug="runcraft",
            created_at=now,
        )
        db.add(merchant)
        db.flush()
    else:
        merchant.name = "RunCraft Athletics"

    # 3. Seed / Upsert Admin User
    admin_user = db.query(AdminUser).filter(AdminUser.email == settings.ADMIN_EMAIL).first()
    if not admin_user:
        admin_user = AdminUser(
            id=DEMO_ADMIN_ID,
            merchant_id=merchant.id,
            email=settings.ADMIN_EMAIL,
            password_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
            created_at=now,
        )
        db.add(admin_user)
    else:
        admin_user.password_hash = hash_password(settings.ADMIN_PASSWORD)
        admin_user.merchant_id = merchant.id

    # 4. Seed / Upsert Merchant Policy
    cross_sell_rules = [
        {
            "trigger_category": "Running Shoes",
            "recommend_category": "Running Socks",
            "reason": "Shoppers buying shoes frequently pair with anti-blister technical socks",
        },
        {
            "trigger_category": "Running Apparel",
            "recommend_category": "Hydration & Accessories",
            "reason": "Recommended gear for training sessions",
        },
    ]
    delivery_rules = {
        "free_delivery_threshold_paise": 200000,  # Free delivery above ₹2,000
        "standard_delivery_paise": 15000,         # ₹150 standard shipping
        "express_delivery_paise": 35000,          # ₹350 express shipping
        "estimated_days_standard": 3,
        "estimated_days_express": 1,
    }

    merchant_policy = db.query(MerchantPolicy).filter(MerchantPolicy.merchant_id == merchant.id).first()
    if not merchant_policy:
        merchant_policy = MerchantPolicy(
            id=DEMO_POLICY_ID,
            merchant_id=merchant.id,
            max_discount_percent=15,
            allow_out_of_stock=False,
            require_purchase_approval=True,
            cross_sell_rules_json=json.dumps(cross_sell_rules),
            delivery_rules_json=json.dumps(delivery_rules),
            updated_at=now,
        )
        db.add(merchant_policy)
    else:
        merchant_policy.max_discount_percent = 15
        merchant_policy.allow_out_of_stock = False
        merchant_policy.require_purchase_approval = True
        merchant_policy.cross_sell_rules_json = json.dumps(cross_sell_rules)
        merchant_policy.delivery_rules_json = json.dumps(delivery_rules)
        merchant_policy.updated_at = now

    # 5. Seed / Upsert 10 Canonical Products
    for item in CANONICAL_PRODUCTS:
        product = db.query(Product).filter(Product.id == item["id"]).first()
        if not product:
            product = Product(
                id=item["id"],
                merchant_id=merchant.id,
                sku=item["sku"],
                name=item["name"],
                category=item["category"],
                short_description=item["short_description"],
                description=item["description"],
                price_paise=item["price_paise"],
                inventory_quantity=item["inventory_quantity"],
                image_url=item["image_url"],
                tags_json=json.dumps(item["tags"]),
                attributes_json=json.dumps(item["attributes"]),
                active=item["active"],
                created_at=now,
                updated_at=now,
            )
            db.add(product)
        else:
            product.merchant_id = merchant.id
            product.sku = item["sku"]
            product.name = item["name"]
            product.category = item["category"]
            product.short_description = item["short_description"]
            product.description = item["description"]
            product.price_paise = item["price_paise"]
            product.inventory_quantity = item["inventory_quantity"]
            product.image_url = item["image_url"]
            product.tags_json = json.dumps(item["tags"])
            product.attributes_json = json.dumps(item["attributes"])
            product.active = item["active"]
            product.updated_at = now

    db.flush()

    # 6. Baseline Demo Data (Orders, Carts, Audits for Analytics & Fulfillment)
    if not catalog_only:
        _seed_baseline_demo_orders(db, merchant.id, now)

    db.commit()
    print(f"[Demo Seed] Successfully seeded RunCraft demo database (Reset={reset}, CatalogOnly={catalog_only})!")


def _seed_baseline_demo_orders(db: Session, merchant_id: str, now: datetime) -> None:
    """
    Seeds a deterministic baseline of 5 confirmed/fulfilled orders, carts, and audit events.
    All demo IDs are prefixed with demo_ to ensure zero conflict with dynamic user sessions.
    """
    # Check if demo orders already exist
    existing_demo_order = db.query(MerchantOrder).filter(MerchantOrder.id == "ord_demo_conf_01").first()
    if existing_demo_order:
        # Already seeded baseline orders
        return

    # Helper addresses
    addr_blr = {
        "line1": "42 Indiranagar, 100ft Road",
        "city": "Bengaluru",
        "state": "Karnataka",
        "postal_code": "560038",
        "country": "India",
    }
    addr_mum = {
        "line1": "12 Marine Drive, Nariman Point",
        "city": "Mumbai",
        "state": "Maharashtra",
        "postal_code": "400021",
        "country": "India",
    }
    addr_del = {
        "line1": "88 Connaught Place, Block B",
        "city": "New Delhi",
        "state": "Delhi",
        "postal_code": "110001",
        "country": "India",
    }
    addr_che = {
        "line1": "15 Anna Salai, T. Nagar",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "postal_code": "600017",
        "country": "India",
    }
    addr_hyd = {
        "line1": "7 Jubilee Hills, Road No 36",
        "city": "Hyderabad",
        "state": "Telangana",
        "postal_code": "500033",
        "country": "India",
    }

    # Order Definitions
    orders_spec = [
        {
            "order_id": "ord_demo_conf_01",
            "cart_id": "cart_demo_sess_01",
            "session_id": "sess_demo_agent_01",
            "channel": "in_app_agent",
            "status": "CONFIRMED",
            "customer": ("Arjun Sharma", "arjun.sharma@example.com", "+919876543210"),
            "address": addr_blr,
            "items": [
                {"product_id": "prod_swiftstride", "sku": "SWIFT-STRIDE-BLU-41", "name": "SwiftStride Daily Trainer", "quantity": 1, "unit_price_paise": 399900, "total_paise": 399900},
                {"product_id": "prod_fleet_socks", "sku": "ACC-FLT-SCK-3PK", "name": "FleetStride Anti-Blister Socks (3-Pack)", "quantity": 1, "unit_price_paise": 69900, "total_paise": 69900},
            ],
            "amount_paise": 469800,  # ₹4,698.00 (Cross-sell pair: Shoes + Socks)
            "time_offset": timedelta(hours=3),
            "carrier": None,
            "tracking": None,
        },
        {
            "order_id": "ord_demo_proc_02",
            "cart_id": "cart_demo_sess_02",
            "session_id": "sess_demo_storefront_02",
            "channel": "direct_storefront",
            "status": "PROCESSING",
            "customer": ("Priya Patel", "priya.p@example.com", "+919812345678"),
            "address": addr_mum,
            "items": [
                {"product_id": "prod_runpro_x2", "sku": "RUN-X2-BLK-42", "name": "RunPro X2 Road Runner", "quantity": 1, "unit_price_paise": 549900, "total_paise": 549900},
            ],
            "amount_paise": 549900,  # ₹5,499.00
            "time_offset": timedelta(days=1),
            "carrier": None,
            "tracking": None,
        },
        {
            "order_id": "ord_demo_ship_03",
            "cart_id": "cart_demo_sess_03",
            "session_id": "ext_buyer_demo_session_03",
            "channel": "external_ai",
            "status": "SHIPPED",
            "customer": ("Rohit Verma", "rohit.v@example.com", "+919988776655"),
            "address": addr_del,
            "items": [
                {"product_id": "prod_carbon_race", "sku": "CARB-RACE-NEON-42", "name": "Carbon Race Elite 3", "quantity": 1, "unit_price_paise": 1499900, "total_paise": 1499900},
                {"product_id": "prod_fleet_socks", "sku": "ACC-FLT-SCK-3PK", "name": "FleetStride Anti-Blister Socks (3-Pack)", "quantity": 1, "unit_price_paise": 69900, "total_paise": 69900},
            ],
            "amount_paise": 1569800,  # ₹15,698.00 (Cross-sell pair: Shoes + Socks)
            "time_offset": timedelta(days=2),
            "carrier": "BlueDart Express",
            "tracking": "BD-8839201",
        },
        {
            "order_id": "ord_demo_deliv_04",
            "cart_id": "cart_demo_sess_04",
            "session_id": "sess_demo_storefront_04",
            "channel": "direct_storefront",
            "status": "DELIVERED",
            "customer": ("Ananya Iyer", "ananya.i@example.com", "+919765432100"),
            "address": addr_che,
            "items": [
                {"product_id": "prod_aerovent_singlet", "sku": "APP-AERO-SGLT-M", "name": "AeroVent Seamless Running Singlet", "quantity": 1, "unit_price_paise": 149900, "total_paise": 149900},
                {"product_id": "prod_paceshorts_5", "sku": "APP-PACE-SHRT-M", "name": "PaceShorts 5\" 2-in-1", "quantity": 1, "unit_price_paise": 189900, "total_paise": 189900},
            ],
            "amount_paise": 339800,  # ₹3,398.00
            "time_offset": timedelta(days=4),
            "carrier": "Delhivery",
            "tracking": "DL-491024",
        },
        {
            "order_id": "ord_demo_deliv_05",
            "cart_id": "cart_demo_sess_05",
            "session_id": "sess_demo_agent_05",
            "channel": "in_app_agent",
            "status": "DELIVERED",
            "customer": ("Vikram Rao", "vikram.r@example.com", "+919845012345"),
            "address": addr_hyd,
            "items": [
                {"product_id": "prod_runpro_x2", "sku": "RUN-X2-BLK-42", "name": "RunPro X2 Road Runner", "quantity": 1, "unit_price_paise": 549900, "total_paise": 549900},
                {"product_id": "prod_flask_500", "sku": "HYD-FLSK-500ML", "name": "HydroGrip 500ml Handheld Flask", "quantity": 1, "unit_price_paise": 89900, "total_paise": 89900},
                {"product_id": "prod_electrolyte_tabs", "sku": "NUT-ELEC-CITRUS-20", "name": "Electrolyte Endurance Tablets (20 Effervescent Tabs)", "quantity": 1, "unit_price_paise": 49900, "total_paise": 49900},
            ],
            "amount_paise": 689700,  # ₹6,897.00
            "time_offset": timedelta(days=5),
            "carrier": "BlueDart Express",
            "tracking": "BD-771294",
        },
    ]

    for spec in orders_spec:
        order_time = now - spec["time_offset"]

        # 1. Cart
        cart = Cart(
            id=spec["cart_id"],
            merchant_id=merchant_id,
            session_id=spec["session_id"],
            status="converted",
            created_at=order_time - timedelta(minutes=15),
            updated_at=order_time,
        )
        db.add(cart)
        db.flush()

        # 2. Cart Items
        for idx, itm in enumerate(spec["items"]):
            cart_item = CartItem(
                id=f"item_{spec['cart_id']}_{idx}",
                cart_id=cart.id,
                product_id=itm["product_id"],
                quantity=itm["quantity"],
                unit_price_paise_snapshot=itm["unit_price_paise"],
                created_at=order_time - timedelta(minutes=10),
                updated_at=order_time - timedelta(minutes=10),
            )
            db.add(cart_item)

        # 3. Order
        confirmed_time = order_time
        processing_time = order_time + timedelta(minutes=20) if spec["status"] in ["PROCESSING", "SHIPPED", "DELIVERED"] else None
        shipped_time = order_time + timedelta(hours=6) if spec["status"] in ["SHIPPED", "DELIVERED"] else None
        delivered_time = order_time + timedelta(days=1) if spec["status"] == "DELIVERED" else None

        order = MerchantOrder(
            id=spec["order_id"],
            merchant_id=merchant_id,
            cart_id=cart.id,
            customer_name=spec["customer"][0],
            customer_email=spec["customer"][1],
            customer_phone=spec["customer"][2],
            shipping_address_json=json.dumps(spec["address"]),
            items_snapshot_json=json.dumps(spec["items"]),
            amount_paise=spec["amount_paise"],
            currency="INR",
            status=spec["status"],
            razorpay_order_id=f"order_rzp_demo_{spec['order_id'][-7:]}",
            approved_at=order_time - timedelta(minutes=2),
            paid_at=order_time,
            confirmed_at=confirmed_time,
            processing_at=processing_time,
            shipped_at=shipped_time,
            delivered_at=delivered_time,
            carrier=spec["carrier"],
            tracking_number=spec["tracking"],
            created_at=order_time,
            updated_at=order_time,
        )
        db.add(order)
        db.flush()

        # 4. Payment Attempt
        payment = PaymentAttempt(
            id=f"pay_{spec['order_id'][-12:]}",
            merchant_order_id=order.id,
            razorpay_order_id=order.razorpay_order_id,
            razorpay_payment_id=f"pay_rzp_demo_{spec['order_id'][-7:]}",
            status="captured",
            signature_verified=True,
            raw_event_reference="demo_seed_payment",
            created_at=order_time,
        )
        db.add(payment)

        # 5. Audit Events
        if spec["channel"] == "in_app_agent":
            db.add(
                AuditEvent(
                    id=f"aud_chat_{spec['order_id'][-7:]}",
                    merchant_id=merchant_id,
                    actor_type="agent",
                    action="agent_chat_turn",
                    entity_type="cart",
                    entity_id=cart.id,
                    session_id=spec["session_id"],
                    metadata_json=json.dumps({"provider": "demo_seed", "tools_executed": ["search_products", "add_to_cart", "get_final_quote"]}),
                    created_at=order_time - timedelta(minutes=8),
                )
            )
        elif spec["channel"] == "external_ai":
            db.add(
                AuditEvent(
                    id=f"aud_mcp_{spec['order_id'][-7:]}",
                    merchant_id=merchant_id,
                    actor_type="external_ai_buyer",
                    action="mcp_tool_called",
                    entity_type="mcp_tool",
                    entity_id="create_checkout",
                    session_id=spec["session_id"],
                    metadata_json=json.dumps({"tool": "create_checkout", "transport": "streamable_http"}),
                    created_at=order_time - timedelta(minutes=5),
                )
            )

        # Payment and Confirmation Audits
        db.add(
            AuditEvent(
                id=f"aud_pay_{spec['order_id'][-7:]}",
                merchant_id=merchant_id,
                actor_type="shopper",
                action="payment_verified",
                entity_type="merchant_order",
                entity_id=order.id,
                session_id=spec["session_id"],
                metadata_json=json.dumps({"amount_paise": spec["amount_paise"], "currency": "INR"}),
                created_at=order_time,
            )
        )
        db.add(
            AuditEvent(
                id=f"aud_conf_{spec['order_id'][-7:]}",
                merchant_id=merchant_id,
                actor_type="system",
                action="order_confirmed",
                entity_type="merchant_order",
                entity_id=order.id,
                session_id=spec["session_id"],
                metadata_json=json.dumps({"status": "CONFIRMED", "amount_paise": spec["amount_paise"]}),
                created_at=order_time,
            )
        )

        # Fulfillment Audits
        if spec["status"] in ["PROCESSING", "SHIPPED", "DELIVERED"]:
            db.add(
                AuditEvent(
                    id=f"aud_proc_{spec['order_id'][-7:]}",
                    merchant_id=merchant_id,
                    actor_type="admin",
                    action="order_processing_started",
                    entity_type="merchant_order",
                    entity_id=order.id,
                    metadata_json=json.dumps({"order_id": order.id, "new_status": "PROCESSING"}),
                    created_at=processing_time,
                )
            )
        if spec["status"] in ["SHIPPED", "DELIVERED"]:
            db.add(
                AuditEvent(
                    id=f"aud_ship_{spec['order_id'][-7:]}",
                    merchant_id=merchant_id,
                    actor_type="admin",
                    action="order_shipped",
                    entity_type="merchant_order",
                    entity_id=order.id,
                    metadata_json=json.dumps({"order_id": order.id, "carrier": spec["carrier"], "tracking_number": spec["tracking"]}),
                    created_at=shipped_time,
                )
            )
        if spec["status"] == "DELIVERED":
            db.add(
                AuditEvent(
                    id=f"aud_del_{spec['order_id'][-7:]}",
                    merchant_id=merchant_id,
                    actor_type="admin",
                    action="order_delivered",
                    entity_type="merchant_order",
                    entity_id=order.id,
                    metadata_json=json.dumps({"order_id": order.id, "new_status": "DELIVERED"}),
                    created_at=delivered_time,
                )
            )

    # 6. Seed 2 Abandoned Carts + 1 Empty Cart for realistic conversion funnel
    cart_ab1 = Cart(
        id="cart_demo_abandoned_01",
        merchant_id=merchant_id,
        session_id="sess_demo_abandoned_01",
        status="active",
        created_at=now - timedelta(days=1, hours=2),
        updated_at=now - timedelta(days=1, hours=2),
    )
    db.add(cart_ab1)
    db.add(
        CartItem(
            id="item_demo_ab1_0",
            cart_id="cart_demo_abandoned_01",
            product_id="prod_flask_500",
            quantity=1,
            unit_price_paise_snapshot=89900,
            created_at=now - timedelta(days=1, hours=2),
            updated_at=now - timedelta(days=1, hours=2),
        )
    )

    cart_ab2 = Cart(
        id="cart_demo_abandoned_02",
        merchant_id=merchant_id,
        session_id="sess_demo_abandoned_02",
        status="active",
        created_at=now - timedelta(days=3),
        updated_at=now - timedelta(days=3),
    )
    db.add(cart_ab2)
    db.add(
        CartItem(
            id="item_demo_ab2_0",
            cart_id="cart_demo_abandoned_02",
            product_id="prod_swiftstride",
            quantity=1,
            unit_price_paise_snapshot=399900,
            created_at=now - timedelta(days=3),
            updated_at=now - timedelta(days=3),
        )
    )

    cart_emp = Cart(
        id="cart_demo_empty_01",
        merchant_id=merchant_id,
        session_id="sess_demo_empty_01",
        status="active",
        created_at=now - timedelta(days=2),
        updated_at=now - timedelta(days=2),
    )
    db.add(cart_emp)


def parse_args():
    parser = argparse.ArgumentParser(description="Deterministic database seeder for RunCraft Agentic Commerce")
    parser.add_argument("--reset", action="store_true", help="Clean reset of demo database before seeding")
    parser.add_argument("--catalog-only", action="store_true", help="Seed only catalog and policies without baseline orders")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    session = SessionLocal()
    try:
        seed_database(session, reset=args.reset, catalog_only=args.catalog_only)
    finally:
        session.close()
