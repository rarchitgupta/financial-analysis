import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


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


class Holding(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: uuid.UUID = Field(index=True)
    symbol: str = Field(index=True)
    quantity: float = Field(gt=0)
    purchase_price: float = Field(gt=0)
    notes: Optional[str] = None
    tags: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def is_fresh(created_at: datetime, ttl_seconds: int) -> bool:
    # Ensure created_at is timezone-aware
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    age_seconds = (datetime.now(timezone.utc) - created_at).total_seconds()
    return age_seconds < ttl_seconds
