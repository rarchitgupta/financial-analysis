import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from app.services.alphavantage import (
    get_quote,
    get_historical_data,
    search_symbols,
    APIError,
)


def _create_async_client_mock(response_data):
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    mock_client.return_value.__aexit__.return_value = None

    return mock_client


@pytest.mark.asyncio
async def test_get_quote_success(mock_quote_response, session_mock):
    with (
        patch(
            "app.services.alphavantage._get_api_key",
            return_value="test_key",
        ),
        patch(
            "app.services.alphavantage.httpx.AsyncClient",
            _create_async_client_mock(mock_quote_response),
        ),
        patch(
            "app.services.alphavantage.storage.get_quote",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch("app.services.alphavantage.storage.save_quote", new_callable=AsyncMock),
    ):
        result = await get_quote("AAPL", session=session_mock)

        assert result["symbol"] == "AAPL"
        assert result["price"] == 150.25
        assert result["timestamp"] == "2025-01-24"


@pytest.mark.asyncio
async def test_get_quote_invalid_symbol(session_mock):
    with (
        patch(
            "app.services.alphavantage._get_api_key",
            return_value="test_key",
        ),
        patch(
            "app.services.alphavantage.httpx.AsyncClient",
            _create_async_client_mock({"Error Message": "Invalid symbol"}),
        ),
        patch(
            "app.services.alphavantage.storage.get_quote",
            new_callable=AsyncMock,
            return_value=None,
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            await get_quote("INVALID", session=session_mock)

        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_get_historical_data_success(mock_history_response, session_mock):
    with (
        patch(
            "app.services.alphavantage._get_api_key",
            return_value="test_key",
        ),
        patch(
            "app.services.alphavantage.httpx.AsyncClient",
            _create_async_client_mock(mock_history_response),
        ),
        patch(
            "app.services.alphavantage.storage.get_history",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.alphavantage.storage.save_history_entries",
            new_callable=AsyncMock,
        ),
    ):
        result = await get_historical_data("AAPL", days=2, session=session_mock)

        assert result["symbol"] == "AAPL"
        assert len(result["data"]) == 2
        assert result["data"][0]["close"] == 150.25


@pytest.mark.asyncio
async def test_search_symbols_success(mock_search_response):
    with (
        patch(
            "app.services.alphavantage._get_api_key",
            return_value="test_key",
        ),
        patch(
            "app.services.alphavantage.httpx.AsyncClient",
            _create_async_client_mock(mock_search_response),
        ),
    ):
        result = await search_symbols("apple")

        assert result["query"] == "apple"
        assert len(result["results"]) == 2
        assert result["results"][0]["symbol"] == "AAPL"
        assert result["results"][0]["name"] == "Apple Inc."


@pytest.mark.asyncio
async def test_search_symbols_no_results():
    with (
        patch(
            "app.services.alphavantage._get_api_key",
            return_value="test_key",
        ),
        patch(
            "app.services.alphavantage.httpx.AsyncClient",
            _create_async_client_mock({"bestMatches": []}),
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            await search_symbols("xyzunknown")

        assert exc_info.value.status_code == 404
