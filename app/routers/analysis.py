from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import User, get_session
from app.models import Holding
from app.schemas.analysis import (
    HoldingAnalysis,
    PortfolioSummary,
    StockAnalysis,
)
from app.services.analysis import (
    AnalysisError,
    calculate_holding_analysis,
    calculate_portfolio_summary,
    calculate_stock_analysis,
)
from app.users import current_active_user

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


async def _handle_analysis_error(coro):
    try:
        return await coro
    except AnalysisError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.get("/stock/{symbol}", response_model=StockAnalysis)
async def analyze_stock(
    symbol: str,
    days: int = Query(30, ge=1, le=252),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    symbol = symbol.upper()
    return await _handle_analysis_error(
        calculate_stock_analysis(symbol, session, days=days)
    )


@router.get("/holdings/{holding_id}", response_model=HoldingAnalysis)
async def analyze_holding(
    holding_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    stmt = select(Holding).where(Holding.id == holding_id)
    result = await session.execute(stmt)
    holding_model = result.scalar_one_or_none()

    if not holding_model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found",
        )

    if holding_model.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    return await _handle_analysis_error(calculate_holding_analysis(holding_id, session))


@router.get("/portfolio", response_model=PortfolioSummary)
async def analyze_portfolio(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    return await _handle_analysis_error(calculate_portfolio_summary(user.id, session))
