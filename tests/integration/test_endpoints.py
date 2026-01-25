from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import create_async_client_mock

client = TestClient(app)


def test_quote_endpoint_success(mock_api_key, mock_quote_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_quote_response),
    ):
        response = client.get("/api/stock/quote/AAPL")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert data["price"] == 150.25


def test_quote_endpoint_invalid_symbol(mock_api_key):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock({"Error Message": "Invalid symbol"}),
    ):
        response = client.get("/api/stock/quote/INVALID")
        assert response.status_code == 404


def test_history_endpoint_success(mock_api_key, mock_history_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_history_response),
    ):
        response = client.get("/api/stock/history/AAPL?days=2")

        assert response.status_code == 200
        data = response.json()
        assert data["symbol"] == "AAPL"
        assert len(data["data"]) == 2


def test_history_endpoint_invalid_symbol(mock_api_key):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock({"Error Message": "Invalid symbol"}),
    ):
        response = client.get("/api/stock/history/INVALID")
        assert response.status_code == 404


def test_search_endpoint_success(mock_api_key, mock_search_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_search_response),
    ):
        response = client.get("/api/stock/search?q=apple")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "apple"
        assert len(data["results"]) == 2


def test_search_endpoint_no_results(mock_api_key):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock({"bestMatches": []}),
    ):
        response = client.get("/api/stock/search?q=xyzunknown")
        assert response.status_code == 404
