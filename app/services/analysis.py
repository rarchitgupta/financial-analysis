import statistics
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import StockHistoryEntry
from app.schemas.analysis import (
    DailyPerformance,
    HoldingAnalysis,
    PortfolioSummary,
    PriceStats,
    StockAnalysis,
)
from app.services.alphavantage import get_quote
from app.storage import get_history
from app.services.holdings import (
    get_holding,
    get_user_holdings,
)


class AnalysisError(Exception):
    pass


async def calculate_price_stats(
    history_data: list[StockHistoryEntry],
) -> PriceStats:
    if not history_data:
        raise AnalysisError("No historical data available for analysis")

    close_prices = [entry.close for entry in history_data]

    average = statistics.mean(close_prices)
    minimum = min(close_prices)
    maximum = max(close_prices)
    std_dev = statistics.stdev(close_prices) if len(close_prices) > 1 else 0.0
    current = close_prices[0]  # Most recent close

    return PriceStats(
        current=current,
        average=average,
        min=minimum,
        max=maximum,
        std_dev=std_dev,
    )


def _calculate_daily_return(open_price: float, close_price: float) -> float:
    if open_price == 0:
        return 0.0
    return ((close_price - open_price) / open_price) * 100


async def calculate_stock_analysis(
    symbol: str,
    session: AsyncSession,
    days: int = 30,
) -> StockAnalysis:
    symbol = symbol.upper()
    history_data = await get_history(session, symbol, limit=days)

    if not history_data:
        raise AnalysisError(f"No historical data found for {symbol}")

    price_stats = await calculate_price_stats(history_data)
    history_data_sorted = sorted(history_data, key=lambda x: x.date)
    daily_performance = [
        DailyPerformance(
            date=entry.date,
            open=entry.open,
            close=entry.close,
            high=entry.high,
            low=entry.low,
            daily_return_pct=_calculate_daily_return(entry.open, entry.close),
        )
        for entry in history_data_sorted
    ]

    if len(history_data_sorted) >= 2:
        first_close = history_data_sorted[0].close
        last_close = history_data_sorted[-1].close
        overall_return_pct = ((last_close - first_close) / first_close) * 100
    else:
        overall_return_pct = 0.0

    return StockAnalysis(
        symbol=symbol,
        period_days=len(history_data),
        price_stats=price_stats,
        daily_performance=daily_performance,
        overall_return_pct=overall_return_pct,
    )


async def calculate_holding_analysis(
    holding_id: int,
    session: AsyncSession,
) -> HoldingAnalysis:
    holding = await get_holding(session, holding_id)

    if not holding:
        raise AnalysisError(f"Holding {holding_id} not found")

    cost_basis = holding.quantity * holding.purchase_price
    current_price = None
    current_value = None
    unrealized_pnl = None
    unrealized_pnl_pct = None

    try:
        quote_data = await get_quote(holding.symbol, session)
        current_price = quote_data.get("price")

        if current_price:
            current_value = holding.quantity * current_price
            unrealized_pnl = current_value - cost_basis
            unrealized_pnl_pct = (
                (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0.0
            )
    except Exception:
        pass

    return HoldingAnalysis(
        holding_id=holding.id,
        symbol=holding.symbol,
        quantity=holding.quantity,
        purchase_price=holding.purchase_price,
        current_price=current_price,
        cost_basis=cost_basis,
        current_value=current_value,
        unrealized_pnl=unrealized_pnl,
        unrealized_pnl_pct=unrealized_pnl_pct,
        notes=holding.notes,
        tags=holding.tags,
    )


async def calculate_portfolio_summary(
    user_id: UUID,
    session: AsyncSession,
) -> PortfolioSummary:
    holdings_data = await get_user_holdings(session, user_id)

    if not holdings_data:
        raise AnalysisError("No holdings found for portfolio analysis")

    holding_analyses = []
    for holding in holdings_data:
        try:
            analysis = await calculate_holding_analysis(holding.id, session)
            holding_analyses.append(analysis)
        except Exception:
            analysis = HoldingAnalysis(
                holding_id=holding.id,
                symbol=holding.symbol,
                quantity=holding.quantity,
                purchase_price=holding.purchase_price,
                cost_basis=holding.quantity * holding.purchase_price,
                notes=holding.notes,
                tags=holding.tags,
            )
            holding_analyses.append(analysis)

    total_holdings = len(holding_analyses)
    total_cost_basis = sum(h.cost_basis for h in holding_analyses)
    total_current_value = sum(h.current_value or 0 for h in holding_analyses)
    total_unrealized_pnl = sum(h.unrealized_pnl or 0 for h in holding_analyses)

    has_current_values = any(h.current_value for h in holding_analyses)
    total_unrealized_pnl_pct = (
        (total_unrealized_pnl / total_cost_basis * 100)
        if (has_current_values and total_cost_basis > 0)
        else None
    )

    performers = [h for h in holding_analyses if h.unrealized_pnl_pct is not None]
    best_performer = (
        max(performers, key=lambda h: h.unrealized_pnl_pct) if performers else None
    )
    worst_performer = (
        min(performers, key=lambda h: h.unrealized_pnl_pct) if performers else None
    )

    return PortfolioSummary(
        total_holdings=total_holdings,
        total_cost_basis=total_cost_basis,
        total_current_value=total_current_value if has_current_values else None,
        total_unrealized_pnl=total_unrealized_pnl if has_current_values else None,
        total_unrealized_pnl_pct=total_unrealized_pnl_pct,
        holdings=holding_analyses,
        best_performer=best_performer,
        worst_performer=worst_performer,
    )
