import os
import httpx

BASE_URL = "https://www.alphavantage.co/query"


class APIError(Exception):
    """Base exception for API errors."""

    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _load_env_if_present() -> None:
    # If python-dotenv is installed and a .env file exists, load it for local development.
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except Exception:
        pass


def _get_api_key() -> str:
    """Get API key, loading env if needed."""
    _load_env_if_present()
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise APIError(502, "AlphaVantage API key not configured")
    return api_key


async def _fetch_json(params: dict) -> dict:
    """Fetch and parse JSON from API, handling network errors."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(BASE_URL, params=params)
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        raise APIError(502, f"API returned status {e.response.status_code}")
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
        raise APIError(503, "Failed to reach AlphaVantage API")


def _check_api_response(data: dict, require_key: str = None) -> dict:
    """Validate API response for errors."""
    if "Note" in data:
        raise APIError(429, "AlphaVantage rate limit reached")
    if "Error Message" in data:
        raise APIError(404, "Invalid symbol")
    if require_key and not (data.get(require_key) or {}):
        raise APIError(404, "No data found in response")
    return data


async def get_quote(symbol: str) -> dict:
    api_key = _get_api_key()
    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}
    data = await _fetch_json(params)
    _check_api_response(data, "Global Quote")

    quote = data["Global Quote"]
    price_s = quote.get("05. price")
    if not price_s:
        raise APIError(404, "Symbol has no price data")

    return {
        "symbol": symbol,
        "price": float(price_s),
        "timestamp": quote.get("07. latest trading day"),
    }


async def get_historical_data(symbol: str, days: int = 30) -> dict:
    """Fetch historical daily price data for a symbol.

    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        days: Number of days of history to return (limited by API data availability)

    Returns:
        Dict with symbol and list of daily prices with dates
    """
    api_key = _get_api_key()
    params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key}
    data = await _fetch_json(params)
    _check_api_response(data, "Time Series (Daily)")

    time_series = data["Time Series (Daily)"]
    history = [
        {
            "date": date,
            "close": float(prices.get("4. close", 0)),
            "high": float(prices.get("2. high", 0)),
            "low": float(prices.get("3. low", 0)),
        }
        for date, prices in list(time_series.items())[:days]
    ]

    return {"symbol": symbol, "data": history}


async def search_symbols(query: str) -> dict:
    """Search for stock symbols by company name or partial symbol.

    Args:
        query: Search term (company name or symbol prefix)

    Returns:
        Dict with list of matching symbols and company info
    """
    api_key = _get_api_key()
    params = {"function": "SYMBOL_SEARCH", "keywords": query, "apikey": api_key}
    data = await _fetch_json(params)
    _check_api_response(data)

    matches = data.get("bestMatches") or []
    if not matches:
        raise APIError(404, "No symbols found matching query")

    results = [
        {
            "symbol": m.get("1. symbol"),
            "name": m.get("2. name"),
            "region": m.get("4. region"),
            "type": m.get("3. type"),
        }
        for m in matches
    ]

    return {"query": query, "results": results}
