import os
import httpx
from dataclasses import dataclass
from functools import wraps
from time import time
from typing import Any, Callable, Union

BASE_URL = "https://www.alphavantage.co/query"


@dataclass
class Success:
    data: dict


@dataclass
class Failure:
    status_code: int
    message: str


# Simple in-memory cache with TTL
_cache: dict[str, tuple[Any, float]] = {}


def cached(ttl_seconds: int) -> Callable:
    """Decorator to cache async function results with TTL.

    Args:
        ttl_seconds: Time-to-live for cache entries in seconds

    Example:
        @cached(ttl_seconds=60)
        async def get_quote(symbol: str) -> dict:
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = f"{func.__name__}:{args}:{kwargs}"

            if cache_key in _cache:
                cached_value, expiry_time = _cache[cache_key]
                if time() < expiry_time:
                    return cached_value
                else:
                    del _cache[cache_key]

            # Call the actual function
            result = await func(*args, **kwargs)

            _cache[cache_key] = (result, time() + ttl_seconds)
            return result

        return wrapper

    return decorator


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


async def _fetch_json(params: dict) -> Union[Success, Failure]:
    """Fetch and parse JSON from API, returning result or failure."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(BASE_URL, params=params)
            if not resp.is_success:
                return Failure(
                    status_code=resp.status_code,
                    message=f"API returned status {resp.status_code}",
                )
            data = resp.json()
            # Check for API errors in the response body (e.g., "Error Message", "Note")
            if "Note" in data:
                return Failure(status_code=429, message=data["Note"])
            if "Error Message" in data:
                return Failure(status_code=400, message=data["Error Message"])
            return Success(data=data)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
        return Failure(status_code=503, message="Failed to reach AlphaVantage API")


def _check_api_response(data: dict, require_key: str = None) -> dict:
    """Validate API response has required data."""
    if require_key and not (data.get(require_key) or {}):
        raise APIError(404, "No data found in response")
    return data


@cached(ttl_seconds=60)
async def get_quote(symbol: str) -> dict:
    """Get current stock price (cached 60 seconds - updates during market hours).

    In production: Would use Redis for distributed cache, with TTL adjusted
    based on market hours (shorter during trading, longer after-hours).
    """
    api_key = _get_api_key()
    params = {"function": "GLOBAL_QUOTE", "symbol": symbol, "apikey": api_key}
    result = await _fetch_json(params)
    if isinstance(result, Failure):
        raise APIError(result.status_code, result.message)
    data = result.data
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


@cached(ttl_seconds=3600)
async def get_historical_data(symbol: str, days: int = 30) -> dict:
    """Fetch historical daily price data for a symbol (cached 1 hour).

    Cached longer than quotes because historical data only changes after market close.

    In production: Would invalidate cache at market close via event system,
    then immediately re-fetch to serve fresh data.

    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        days: Number of days of history to return (limited by API data availability)

    Returns:
        Dict with symbol and list of daily prices with dates
    """
    api_key = _get_api_key()
    params = {"function": "TIME_SERIES_DAILY", "symbol": symbol, "apikey": api_key}
    result = await _fetch_json(params)
    if isinstance(result, Failure):
        raise APIError(result.status_code, result.message)
    data = result.data
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


@cached(ttl_seconds=86400)
async def search_symbols(query: str) -> dict:
    """Search for stock symbols by company name or partial symbol (cached 24 hours).

    Cached longest because company names and symbols rarely change.

    In production: Precompute and cache all popular searches, fallback to
    Redis with very high TTL (days/weeks) for unpopular queries.

    Args:
        query: Search term (company name or symbol prefix)

    Returns:
        Dict with list of matching symbols and company info
    """
    api_key = _get_api_key()
    params = {"function": "SYMBOL_SEARCH", "keywords": query, "apikey": api_key}
    result = await _fetch_json(params)
    if isinstance(result, Failure):
        raise APIError(result.status_code, result.message)
    data = result.data
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
