from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "agentic-commerce"
    assert "version" in data


def test_get_products():
    response = client.get("/api/products")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert isinstance(res["data"], list)
    assert len(res["data"]) >= 10

    # Verify first product shape
    prod = res["data"][0]
    assert "id" in prod
    assert "sku" in prod
    assert "name" in prod
    assert "price_paise" in prod
    assert isinstance(prod["price_paise"], int)
    assert prod["price_paise"] > 0
    assert "inventory_quantity" in prod
    assert "tags" in prod
    assert isinstance(prod["tags"], list)
    assert "attributes" in prod
    assert isinstance(prod["attributes"], dict)
    assert prod["active"] is True


def test_product_filtering():
    # Filter by category
    response = client.get("/api/products?category=Shoes")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert len(res["data"]) > 0
    for p in res["data"]:
        assert "Shoes" in p["category"]

    # Filter by max_price_paise (e.g. <= 600000 paise = ₹6000)
    response_price = client.get("/api/products?max_price_paise=600000")
    assert response_price.status_code == 200
    res_price = response_price.json()
    for p in res_price["data"]:
        assert p["price_paise"] <= 600000


def test_get_single_product():
    response = client.get("/api/products/prod_runpro_x2")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert res["data"]["sku"] == "RUN-X2-BLK-42"
    assert res["data"]["name"] == "RunPro X2 Road Runner"


if __name__ == "__main__":
    print("Running Phase 0 verification tests...")
    test_health_endpoint()
    print("[OK] Health check passed")
    test_get_products()
    print("[OK] Products list endpoint passed (10 seeded products)")
    test_product_filtering()
    print("[OK] Category & price filter passed")
    test_get_single_product()
    print("[OK] Single product lookup passed")
    print("All Phase 0 tests passed successfully!")
