import pytest
from unittest.mock import patch

from app.services.alphavantage import (
    get_quote,
    get_historical_data,
    search_symbols,
    APIError,
)
from tests.conftest import create_async_client_mock


@pytest.mark.asyncio
async def test_get_quote_success(mock_api_key, mock_quote_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_quote_response),
    ):
        result = await get_quote("AAPL")

        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.25
        assert result["timestamp"] == "2025-01-24"


@pytest.mark.asyncio
async def test_get_quote_invalid_symbol(mock_api_key):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock({"Error Message": "Invalid symbol"}),
    ):
        with pytest.raises(APIError) as exc_info:
            await get_quote("INVALID")

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_historical_data_success(mock_api_key, mock_history_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_history_response),
    ):
        result = await get_historical_data("AAPL", days=2)

        assert result["symbol"] == "AAPL"
        assert len(result["data"]) == 2
        assert result["data"][0]["close"] == 150.25


@pytest.mark.asyncio
async def test_search_symbols_success(mock_api_key, mock_search_response):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock(mock_search_response),
    ):
        result = await search_symbols("apple")

        assert result["query"] == "apple"
        assert len(result["results"]) == 2
        assert result["results"][0]["symbol"] == "AAPL"
        assert result["results"][0]["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_search_symbols_no_results(mock_api_key):
    with patch(
        "app.services.alphavantage.httpx.AsyncClient",
        create_async_client_mock({"bestMatches": []}),
    ):
        with pytest.raises(APIError) as exc_info:
            await search_symbols("xyzunknown")

        assert exc_info.value.status_code == 404
