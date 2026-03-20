from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


def _create_async_client_mock(response_data):
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.is_success = True

    mock_client = MagicMock()
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    mock_client.return_value.__aexit__.return_value = None

    return mock_client


def test_analyze_stock_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.get("/api/analysis/stock/AAPL")
    assert response.status_code == 401


def test_analyze_holding_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.get("/api/analysis/holdings/1")
    assert response.status_code == 401


def test_analyze_portfolio_requires_auth(client_unauthenticated: TestClient):
    response = client_unauthenticated.get("/api/analysis/portfolio")
    assert response.status_code == 401


def test_analyze_stock_no_data(client: TestClient, mock_api_key):
    response = client.get("/api/analysis/stock/NONEXISTENT")
    assert response.status_code == 404
    assert "No historical data found" in response.json()["detail"]


def test_analyze_stock_with_data(
    client: TestClient, mock_api_key, mock_history_response
):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_history_response),
    ):
        response = client.get("/api/stock/history/AAPL?days=2")
        assert response.status_code == 200

    response = client.get("/api/analysis/stock/AAPL?days=2")
    assert response.status_code == 200
    data = response.json()

    assert data["symbol"] == "AAPL"
    assert data["period_days"] == 2
    assert "price_stats" in data
    assert "daily_performance" in data

    stats = data["price_stats"]
    assert "current" in stats
    assert "average" in stats
    assert "min" in stats
    assert "max" in stats
    assert "std_dev" in stats

    assert len(data["daily_performance"]) == 2
    for perf in data["daily_performance"]:
        assert "date" in perf
        assert "open" in perf
        assert "close" in perf
        assert "daily_return_pct" in perf

    assert "overall_return_pct" in data


def test_analyze_stock_days_validation(client: TestClient, mock_api_key):
    response = client.get("/api/analysis/stock/AAPL?days=500")
    assert response.status_code == 422

    response = client.get("/api/analysis/stock/AAPL?days=0")
    assert response.status_code == 422


def test_analyze_holding_not_found(client: TestClient, mock_api_key):
    response = client.get("/api/analysis/holdings/999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_analyze_holding_with_data(
    client: TestClient, mock_api_key, mock_quote_response
):
    response = client.post(
        "/api/holdings",
        json={
            "symbol": "AAPL",
            "quantity": 10,
            "purchase_price": 150.0,
            "notes": "Test holding",
            "tags": "tech",
        },
    )
    assert response.status_code == 201
    holding_id = response.json()["id"]

    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_quote_response),
    ):
        response = client.get(f"/api/analysis/holdings/{holding_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["holding_id"] == holding_id
        assert data["symbol"] == "AAPL"
        assert data["quantity"] == 10
        assert data["purchase_price"] == 150.0
        assert data["cost_basis"] == 1500.0
        assert data["current_price"] == 150.25
        assert data["current_value"] == 1502.5
        assert data["notes"] == "Test holding"
        assert data["tags"] == "tech"
        assert data["unrealized_pnl"] == 2.5
        assert abs(data["unrealized_pnl_pct"] - 0.1667) < 0.01


def test_analyze_portfolio_no_holdings(client: TestClient, mock_api_key):
    response = client.get("/api/analysis/portfolio")
    assert response.status_code == 404
    assert "No holdings found" in response.json()["detail"]


def test_analyze_portfolio_with_holdings(
    client: TestClient, mock_api_key, mock_quote_response
):
    holdings_data = [
        {"symbol": "AAPL", "quantity": 10, "purchase_price": 150.0},
        {"symbol": "GOOGL", "quantity": 5, "purchase_price": 2800.0},
    ]

    holding_ids = []
    for data in holdings_data:
        response = client.post("/api/holdings", json=data)
        assert response.status_code == 201
        holding_ids.append(response.json()["id"])

    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_quote_response),
    ):
        response = client.get("/api/analysis/portfolio")
        assert response.status_code == 200

        data = response.json()
        assert data["total_holdings"] == 2
        assert data["total_cost_basis"] == 1500.0 + 14000.0
        assert "total_current_value" in data
        assert "total_unrealized_pnl" in data
        assert "holdings" in data
        assert len(data["holdings"]) == 2
        assert "best_performer" in data
        assert "worst_performer" in data


def test_analyze_stock_symbol_case_insensitive(client: TestClient, mock_api_key):
    response = client.get("/api/analysis/stock/aapl")
    assert response.status_code == 404
