import os
import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.fixture
def mock_api_key():
    with patch.dict(os.environ, {"ALPHAVANTAGE_API_KEY": "test_key"}):
        yield "test_key"


@pytest.fixture
def mock_quote_response():
    return {
        "Global Quote": {
            "01. symbol": "AAPL",
            "05. price": "150.25",
            "07. latest trading day": "2025-01-24",
        }
    }


@pytest.fixture
def mock_history_response():
    return {
        "Time Series (Daily)": {
            "2025-01-24": {
                "1. open": "149.50",
                "2. high": "151.00",
                "3. low": "149.50",
                "4. close": "150.25",
            },
            "2025-01-23": {
                "1. open": "148.75",
                "2. high": "150.00",
                "3. low": "148.50",
                "4. close": "149.75",
            },
        }
    }


@pytest.fixture
def mock_search_response():
    return {
        "bestMatches": [
            {
                "1. symbol": "AAPL",
                "2. name": "Apple Inc.",
                "3. type": "Equity",
                "4. region": "United States",
            },
            {
                "1. symbol": "AAPL.L",
                "2. name": "Apple Inc.",
                "3. type": "Equity",
                "4. region": "United Kingdom",
            },
        ]
    }


def create_async_client_mock(response_data):
    """Helper to create a properly mocked AsyncClient context manager."""
    mock_response = MagicMock()
    mock_response.json.return_value = response_data
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.return_value.__aenter__.return_value.get = AsyncMock(
        return_value=mock_response
    )
    mock_client.return_value.__aexit__.return_value = None

    return mock_client


@pytest.fixture
def mock_http_client(mock_api_key):
    with patch("app.services.alphavantage.httpx.AsyncClient") as mock_client:
        yield mock_client
