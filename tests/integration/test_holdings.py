from fastapi.testclient import TestClient


def test_create_holding_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.post(
        "/api/holdings",
        json={
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.25,
        },
    )
    assert response.status_code == 401


def test_list_holdings_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.get("/api/holdings")
    assert response.status_code == 401


def test_get_holding_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.get("/api/holdings/1")
    assert response.status_code == 401


def test_update_holding_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.put(
        "/api/holdings/1",
        json={"quantity": 20},
    )
    assert response.status_code == 401


def test_delete_holding_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.delete("/api/holdings/1")
    assert response.status_code == 401


def test_create_holding(client: TestClient, test_user):
    response = client.post(
        "/api/holdings",
        json={
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.25,
            "notes": "Long-term hold",
            "tags": "tech,growth",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["symbol"] == "AAPL"
    assert data["quantity"] == 10.0
    assert data["user_id"] == str(test_user.id)


def test_list_holdings(client: TestClient, test_user):
    client.post(
        "/api/holdings",
        json={
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.25,
        },
    )
    response = client.get("/api/holdings")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["symbol"] == "AAPL"


def test_get_holding(client: TestClient):
    create_response = client.post(
        "/api/holdings",
        json={
            "symbol": "GOOGL",
            "quantity": 5,
            "purchase_price": 2800.0,
        },
    )
    holding_id = create_response.json()["id"]

    response = client.get(f"/api/holdings/{holding_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == holding_id
    assert data["symbol"] == "GOOGL"


def test_update_holding(client: TestClient):
    create_response = client.post(
        "/api/holdings",
        json={
            "symbol": "MSFT",
            "quantity": 5,
            "purchase_price": 300.0,
        },
    )
    holding_id = create_response.json()["id"]

    response = client.put(
        f"/api/holdings/{holding_id}",
        json={"quantity": 10},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["quantity"] == 10.0


def test_delete_holding(client: TestClient):
    create_response = client.post(
        "/api/holdings",
        json={
            "symbol": "TSLA",
            "quantity": 2,
            "purchase_price": 250.0,
        },
    )
    holding_id = create_response.json()["id"]

    response = client.delete(f"/api/holdings/{holding_id}")
    assert response.status_code == 204

    response = client.get(f"/api/holdings/{holding_id}")
    assert response.status_code == 404


def test_holding_not_found(client: TestClient):
    response = client.get("/api/holdings/999")
    assert response.status_code == 404
