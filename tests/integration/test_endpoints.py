"""Integration tests for FastAPI endpoints."""

from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


def _create_async_client_mock(response_data):
    """Helper to mock httpx.AsyncClient for API calls."""
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    mock_client.return_value.__aexit__.return_value = None

    return mock_client


def test_quote_endpoint_success(client: TestClient, mock_api_key, mock_quote_response):
    """Test getting a stock quote successfully."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_quote_response),
    ):
        response = client.get("/api/stock/quote/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.25


def test_quote_endpoint_invalid_symbol(client: TestClient, mock_api_key):
    """Test error handling for invalid symbol."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock({"Error Message": "Invalid symbol"}),
    ):
        response = client.get("/api/stock/quote/INVALID")
        assert response.status_code == 400


def test_history_endpoint_success(
    client: TestClient, mock_api_key, mock_history_response
):
    """Test getting historical data successfully."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_history_response),
    ):
        response = client.get("/api/stock/history/AAPL?days=2")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert len(data["data"]) == 2


def test_history_endpoint_invalid_symbol(client: TestClient, mock_api_key):
    """Test error handling for historical data."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock({"Error Message": "Invalid symbol"}),
    ):
        response = client.get("/api/stock/history/INVALID")
        assert response.status_code == 400


def test_search_endpoint_success(
    client: TestClient, mock_api_key, mock_search_response
):
    """Test searching for symbols successfully."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock(mock_search_response),
    ):
        response = client.get("/api/stock/search?q=apple")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "apple"
        assert len(data["results"]) == 2


def test_search_endpoint_no_results(client: TestClient, mock_api_key):
    """Test search with no results."""
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        _create_async_client_mock({"bestMatches": []}),
    ):
        response = client.get("/api/stock/search?q=xyzunknown")
        assert response.status_code == 404
