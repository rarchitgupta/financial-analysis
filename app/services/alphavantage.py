import os
import httpx
from dataclasses import dataclass
from typing import Union
from sqlalchemy.ext.asyncio import AsyncSession

from app import storage
from app.models import is_fresh

BASE_URL = "https://www.alphavantage.co/query"


@dataclass
class Success:
    data: dict


@dataclass
class Failure:
    status_code: int
    message: str


_cache: dict = {}


class APIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _load_env_if_present() -> None:
    try:
        from dotenv import load_dotenv

        load_dotenv(override=False)
    except Exception:
        pass


def _get_api_key() -> str:
    _load_env_if_present()
    api_key = os.getenv("ALPHAVANTAGE_API_KEY")
    if not api_key:
        raise APIError(502, "AlphaVantage API key not configured")
    return api_key


async def _fetch_json(params: dict) -> Union[Success, Failure]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(BASE_URL, params=params)
            if not resp.is_success:
                return Failure(
                    status_code=resp.status_code,
                    message=f"API returned status {resp.status_code}",
                )
            data = resp.json()
            if "Note" in data:
                return Failure(status_code=429, message=data["Note"])
            if "Error Message" in data:
                return Failure(status_code=400, message=data["Error Message"])
            return Success(data=data)
    except (httpx.ConnectError, httpx.TimeoutException, httpx.RequestError):
        return Failure(status_code=503, message="Failed to reach AlphaVantage API")


def _check_api_response(data: dict, require_key: str = None) -> dict:
    if require_key and not (data.get(require_key) or {}):
        raise APIError(404, "No data found in response")
    return data


async def get_quote(symbol: str, session: AsyncSession) -> dict:
    db_quote = await storage.get_quote(session, symbol)
    if db_quote and is_fresh(db_quote.created_at, ttl_seconds=60):
        return db_quote.model_dump()

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

    timestamp = quote.get("07. latest trading day")
    await storage.save_quote(session, symbol, float(price_s), timestamp)

    return {
        "symbol": symbol,
        "price": float(price_s),
        "timestamp": timestamp,
    }


async def get_historical_data(
    symbol: str, session: AsyncSession, days: int = 30
) -> dict:
    db_history = await storage.get_history(session, symbol, limit=days)
    if db_history and is_fresh(db_history[0].created_at, ttl_seconds=3600):
        return {
            "symbol": symbol,
            "data": [
                {
                    "date": entry.date,
                    "close": entry.close,
                    "high": entry.high,
                    "low": entry.low,
                    "open": entry.open,
                }
                for entry in db_history
            ],
        }

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
            "open": float(prices.get("1. open", 0)),
        }
        for date, prices in list(time_series.items())[:days]
    ]

    await storage.save_history_entries(session, symbol, history)

    return {"symbol": symbol, "data": history}


async def search_symbols(query: str) -> dict:
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
