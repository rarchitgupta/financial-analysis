from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Holding
from app.schemas import HoldingCreate, HoldingRead, HoldingUpdate


async def create_holding(
    session: AsyncSession, user_id: UUID, holding_data: HoldingCreate
) -> HoldingRead:
    holding = Holding(
        user_id=user_id,
        symbol=holding_data.symbol.upper(),
        quantity=holding_data.quantity,
        purchase_price=holding_data.purchase_price,
        notes=holding_data.notes,
        tags=holding_data.tags,
    )
    session.add(holding)
    await session.commit()
    await session.refresh(holding)
    return HoldingRead.model_validate(holding)


async def get_holding(session: AsyncSession, holding_id: int) -> HoldingRead | None:
    stmt = select(Holding).where(Holding.id == holding_id)
    result = await session.execute(stmt)
    holding = result.scalar_one_or_none()
    return HoldingRead.model_validate(holding) if holding else None


async def get_user_holdings(session: AsyncSession, user_id: UUID) -> list[HoldingRead]:
    stmt = select(Holding).where(Holding.user_id == user_id)
    result = await session.execute(stmt)
    holdings = result.scalars().all()
    return [HoldingRead.model_validate(h) for h in holdings]


async def update_holding(
    session: AsyncSession, holding_id: int, update_data: HoldingUpdate
) -> HoldingRead | None:
    stmt = select(Holding).where(Holding.id == holding_id)
    result = await session.execute(stmt)
    holding = result.scalar_one_or_none()

    if not holding:
        return None

    if update_data.quantity is not None:
        holding.quantity = update_data.quantity
    if update_data.purchase_price is not None:
        holding.purchase_price = update_data.purchase_price
    if update_data.notes is not None:
        holding.notes = update_data.notes
    if update_data.tags is not None:
        holding.tags = update_data.tags

    holding.updated_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(holding)
    return HoldingRead.model_validate(holding)


async def delete_holding(session: AsyncSession, holding_id: int) -> bool:
    stmt = select(Holding).where(Holding.id == holding_id)
    result = await session.execute(stmt)
    holding = result.scalar_one_or_none()

    if not holding:
        return False

    await session.delete(holding)
    await session.commit()
    return True
