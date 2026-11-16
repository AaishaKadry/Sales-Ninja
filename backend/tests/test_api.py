def payload(order_id="T-100"):
    return {"order_id": order_id, "order_date": "2026-01-12", "customer": "Asha",
            "product": "Wireless Mouse", "category": "Electronics", "region": "North",
            "quantity": 2, "unit_price": 500, "unit_cost": 250}

def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"

def test_create_and_duplicate(client):
    assert client.post("/api/sales", json=payload()).status_code == 201
    assert client.post("/api/sales", json=payload()).status_code == 409

def test_summary(client):
    client.post("/api/sales", json=payload())
    result = client.get("/api/analytics/summary").json()
    assert result["revenue"] == 1000
    assert result["profit"] == 500
    assert result["orders"] == 1

def test_delete(client):
    created = client.post("/api/sales", json=payload()).json()
    assert client.delete(f"/api/sales/{created['id']}").status_code == 204
    assert client.get("/api/sales").json() == []
