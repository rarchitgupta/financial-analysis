from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_session
from app.services.alphavantage import (
    APIError,
    get_historical_data as av_get_historical_data,
    get_quote as av_get_quote,
    search_symbols as av_search_symbols,
)
from app.users import current_active_user

router = APIRouter(prefix="/api/stock", tags=["stock"])


async def _call_service(coro):
    try:
        return await coro
    except APIError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@router.get("/quote/{symbol}")
async def quote(
    symbol: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    symbol = symbol.upper()
    return await _call_service(av_get_quote(symbol, session=session))


@router.get("/history/{symbol}")
async def history(
    symbol: str,
    days: int = Query(30, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    symbol = symbol.upper()
    return await _call_service(
        av_get_historical_data(symbol, days=days, session=session)
    )


@router.get("/search")
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    user: User = Depends(current_active_user),
):
    return await _call_service(av_search_symbols(q))
