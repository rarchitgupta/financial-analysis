from fastapi import APIRouter, HTTPException, Query

from app.services.alphavantage import (
    get_quote as av_get_quote,
    get_historical_data as av_get_historical_data,
    search_symbols as av_search_symbols,
    APIError,
)

router = APIRouter()


def _handle_api_error(e: APIError) -> None:
    """Convert APIError to HTTPException."""
    raise HTTPException(status_code=e.status_code, detail=e.message)


async def _call_service(coro):
    """Execute service coroutine and handle errors."""
    try:
        return await coro
    except APIError as e:
        _handle_api_error(e)


@router.get("/api/stock/quote/{symbol}")
async def quote(symbol: str):
    symbol = symbol.upper()
    return await _call_service(av_get_quote(symbol))


@router.get("/api/stock/history/{symbol}")
async def history(symbol: str, days: int = Query(30, ge=1, le=100)):
    """Get historical daily price data for a symbol.

    Args:
        symbol: Stock symbol (e.g., AAPL)
        days: Number of days of history (1-100, default 30)
    """
    symbol = symbol.upper()
    return await _call_service(av_get_historical_data(symbol, days=days))


@router.get("/api/stock/search")
async def search(q: str = Query(..., min_length=1, max_length=100)):
    """Search for stock symbols by company name or symbol prefix.

    Args:
        q: Search query (company name or symbol)
    """
    return await _call_service(av_search_symbols(q))
