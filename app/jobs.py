import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db import AsyncSessionLocal, User
from app.models import Holding
from app.services.alphavantage import get_quote
from app.services.analysis import calculate_portfolio_summary

logger = logging.getLogger(__name__)


async def refresh_quotes() -> None:
    """Refresh stock quotes for all tracked symbols."""
    session: AsyncSession
    async with AsyncSessionLocal() as session:
        try:
            # Get distinct symbols from user holdings
            stmt = select(Holding.symbol).distinct()
            result = await session.execute(stmt)
            symbols = result.scalars().all()

            if not symbols:
                logger.debug("No symbols to refresh")
                return

            logger.info(f"Refreshing quotes for {len(symbols)} symbols")

            for symbol in symbols:
                try:
                    await get_quote(symbol, session)
                    logger.debug(f"Refreshed quote for {symbol}")
                except Exception as e:
                    logger.warning(f"Failed to refresh quote for {symbol}: {str(e)}")

        except Exception as e:
            logger.error(f"Error in refresh_quotes job: {str(e)}")


async def recalculate_aggregates() -> None:
    """Pre-calculate portfolio aggregates for all users."""
    session: AsyncSession
    async with AsyncSessionLocal() as session:
        try:
            # Get all users
            stmt = select(User)
            result = await session.execute(stmt)
            users = result.scalars().all()

            if not users:
                logger.debug("No users to recalculate aggregates for")
                return

            logger.info(f"Recalculating aggregates for {len(users)} users")

            for user in users:
                try:
                    await calculate_portfolio_summary(user.id, session)
                    logger.debug(f"Recalculated aggregates for user {user.id}")
                except Exception as e:
                    logger.debug(f"User {user.id} has no holdings or error: {str(e)}")

        except Exception as e:
            logger.error(f"Error in recalculate_aggregates job: {str(e)}")
