from typing import Optional
from pydantic import BaseModel, Field


class PriceStats(BaseModel):
    current: float
    average: float
    minimum: float = Field(..., alias="min")
    maximum: float = Field(..., alias="max")
    std_dev: float

    model_config = {"populate_by_name": True}


class DailyPerformance(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    daily_return_pct: float


class StockAnalysis(BaseModel):
    symbol: str
    period_days: int
    price_stats: PriceStats
    daily_performance: list[DailyPerformance]
    overall_return_pct: float


class HoldingAnalysis(BaseModel):
    holding_id: int
    symbol: str
    quantity: float
    purchase_price: float
    current_price: Optional[float] = None
    cost_basis: float
    current_value: Optional[float] = None
    unrealized_pnl: Optional[float] = None
    unrealized_pnl_pct: Optional[float] = None
    notes: Optional[str] = None
    tags: Optional[str] = None


class PortfolioSummary(BaseModel):
    total_holdings: int
    total_cost_basis: float
    total_current_value: Optional[float] = None
    total_unrealized_pnl: Optional[float] = None
    total_unrealized_pnl_pct: Optional[float] = None
    holdings: list[HoldingAnalysis]
    best_performer: Optional[HoldingAnalysis] = None
    worst_performer: Optional[HoldingAnalysis] = None
