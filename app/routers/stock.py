from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.alphavantage import (
    get_quote as av_get_quote,
    get_historical_data as av_get_historical_data,
    search_symbols as av_search_symbols,
    APIError,
)
from app.db import get_session

router = APIRouter()


def _handle_api_error(e: APIError) -> None:
    raise HTTPException(status_code=e.status_code, detail=e.message)


async def _call_service(coro):
    try:
        return await coro
    except APIError as e:
        _handle_api_error(e)


@router.get("/api/stock/quote/{symbol}")
async def quote(symbol: str, session: AsyncSession = Depends(get_session)):
    symbol = symbol.upper()
    return await _call_service(av_get_quote(symbol, session=session))


@router.get("/api/stock/history/{symbol}")
async def history(
    symbol: str,
    days: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    symbol = symbol.upper()
    return await _call_service(
        av_get_historical_data(symbol, days=days, session=session)
    )


@router.get("/api/stock/search")
async def search(q: str = Query(..., min_length=1, max_length=100)):
    return await _call_service(av_search_symbols(q))
