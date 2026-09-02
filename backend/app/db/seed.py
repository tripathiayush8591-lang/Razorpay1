import json
import uuid
import hashlib
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.merchant import Merchant
from app.models.admin_user import AdminUser
from app.models.product import Product
from app.models.policy import MerchantPolicy


def hash_password(password: str) -> str:
    try:
        import bcrypt
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    except Exception:
        # Fallback to salted sha256 for demo environment if bcrypt binary has issues
        salt = "runcraft_demo_salt"
        return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def seed_database(db: Session) -> None:
    # 1. Create tables if not present
    Base.metadata.create_all(bind=engine)

    # 2. Check if already seeded
    existing_merchant = db.query(Merchant).filter(Merchant.slug == "runcraft").first()
    if existing_merchant:
        print("Database already seeded with merchant 'runcraft'. Resetting catalog and policies...")
        db.query(Product).filter(Product.merchant_id == existing_merchant.id).delete()
        db.query(MerchantPolicy).filter(MerchantPolicy.merchant_id == existing_merchant.id).delete()
        # Update admin user password hash with bcrypt if needed
        admin_user = db.query(AdminUser).filter(AdminUser.email == "admin@runcraft.internal").first()
        if admin_user:
            admin_user.password_hash = hash_password("demosecret123")
        merchant = existing_merchant
    else:
        merchant_id = f"merch_{uuid.uuid4().hex[:12]}"
        merchant = Merchant(
            id=merchant_id,
            name="RunCraft Athletics",
            slug="runcraft",
            created_at=datetime.now(timezone.utc),
        )
        db.add(merchant)
        db.flush()

        # Seed Admin User
        admin_id = f"admin_{uuid.uuid4().hex[:12]}"
        admin_user = AdminUser(
            id=admin_id,
            merchant_id=merchant.id,
            email="admin@runcraft.internal",
            password_hash=hash_password("demosecret123"),
            role="admin",
            created_at=datetime.now(timezone.utc),
        )
        db.add(admin_user)

    # 3. Seed Merchant Policy
    policy_id = f"pol_{uuid.uuid4().hex[:12]}"
    cross_sell_rules = [
        {"trigger_category": "Running Shoes", "recommend_category": "Running Socks", "reason": "Shoppers buying shoes frequently pair with anti-blister technical socks"},
        {"trigger_category": "Running Apparel", "recommend_category": "Hydration & Accessories", "reason": "Recommended gear for training sessions"},
    ]
    delivery_rules = {
        "free_delivery_threshold_paise": 200000,  # Free above ₹2,000
        "standard_delivery_paise": 15000,         # ₹150 standard shipping
        "express_delivery_paise": 35000,          # ₹350 express shipping
        "estimated_days_standard": 3,
        "estimated_days_express": 1,
    }

    merchant_policy = MerchantPolicy(
        id=policy_id,
        merchant_id=merchant.id,
        max_discount_percent=15,
        allow_out_of_stock=False,
        require_purchase_approval=True,
        cross_sell_rules_json=json.dumps(cross_sell_rules),
        delivery_rules_json=json.dumps(delivery_rules),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(merchant_policy)

    # 4. Seed 10 Realistic Products
    catalog = [
        {
            "id": "prod_runpro_x2",
            "sku": "RUN-X2-BLK-42",
            "name": "RunPro X2 Road Runner",
            "category": "Running Shoes",
            "short_description": "Lightweight, responsive road running shoes built for beginner to intermediate runners.",
            "description": "Engineered with dual-density foam for plush shock absorption and high energy return. Breathable jacquard mesh upper keeps feet cool during long morning runs.",
            "price_paise": 549900,  # ₹5,499.00
            "inventory_quantity": 25,
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
            "inventory_quantity": 30,
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
            "inventory_quantity": 8,
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
            "inventory_quantity": 40,
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
            "inventory_quantity": 35,
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
            "inventory_quantity": 60,
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
            "inventory_quantity": 45,
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
            "inventory_quantity": 50,
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
            "inventory_quantity": 80,
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
            "inventory_quantity": 55,
            "image_url": "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=800&auto=format&fit=crop&q=60",
            "tags": ["recovery", "massage", "accessories", "plantar-fasciitis"],
            "attributes": {"diameter_mm": 63, "material": "High Density Natural Rubber"},
            "active": True,
        },
    ]

    for item in catalog:
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
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(product)

    db.commit()
    print(f"Successfully seeded database for merchant '{merchant.name}' with {len(catalog)} products and policies!")


if __name__ == "__main__":
    session = SessionLocal()
    try:
        seed_database(session)
    finally:
        session.close()
