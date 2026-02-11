"""Database models for financial data."""

from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional


class StockQuote(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    price: float
    timestamp: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class StockHistoryEntry(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: str = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def is_fresh(created_at: datetime, ttl_seconds: int) -> bool:
    age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    return age_seconds < ttl_seconds
