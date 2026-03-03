from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class HoldingCreate(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=10)
    quantity: float = Field(..., gt=0)
    purchase_price: float = Field(..., gt=0)
    notes: Optional[str] = Field(None, max_length=500)
    tags: Optional[str] = Field(None, max_length=200)


class HoldingRead(BaseModel):
    id: int
    user_id: UUID
    symbol: str
    quantity: float
    purchase_price: float
    notes: Optional[str]
    tags: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class HoldingUpdate(BaseModel):
    quantity: Optional[float] = Field(None, gt=0)
    purchase_price: Optional[float] = Field(None, gt=0)
    notes: Optional[str] = Field(None, max_length=500)
    tags: Optional[str] = Field(None, max_length=200)
