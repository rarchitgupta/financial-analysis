from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import StockQuote, StockHistoryEntry


async def save_quote(
    session: AsyncSession, symbol: str, price: float, timestamp: str
) -> StockQuote:
    stmt = select(StockQuote).where(StockQuote.symbol == symbol)
    result = await session.execute(stmt)
    quote = result.scalar_one_or_none()

    if quote:
        quote.price = price
        quote.timestamp = timestamp
    else:
        quote = StockQuote(symbol=symbol, price=price, timestamp=timestamp)
        session.add(quote)

    await session.commit()
    await session.refresh(quote)
    return quote


async def get_quote(session: AsyncSession, symbol: str) -> StockQuote | None:
    stmt = select(StockQuote).where(StockQuote.symbol == symbol)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def save_history_entries(
    session: AsyncSession, symbol: str, history_data: list[dict]
) -> list[StockHistoryEntry]:
    stmt = select(StockHistoryEntry).where(StockHistoryEntry.symbol == symbol)
    result = await session.execute(stmt)
    old_entries = result.scalars().all()
    for entry in old_entries:
        await session.delete(entry)

    entries = []
    for data in history_data:
        entry = StockHistoryEntry(
            symbol=symbol,
            date=data["date"],
            open=data["open"],
            high=data["high"],
            low=data["low"],
            close=data["close"],
        )
        session.add(entry)
        entries.append(entry)

    await session.commit()
    for entry in entries:
        await session.refresh(entry)

    return entries


async def get_history(
    session: AsyncSession, symbol: str, limit: int = 30
) -> list[StockHistoryEntry]:
    stmt = (
        select(StockHistoryEntry)
        .where(StockHistoryEntry.symbol == symbol)
        .order_by(StockHistoryEntry.date.desc())
        .limit(limit)
    )
    result = await session.execute(stmt)
    return result.scalars().all()
