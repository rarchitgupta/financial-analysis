from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import User, get_session
from app.schemas import HoldingCreate, HoldingRead, HoldingUpdate
from app.services.holdings import (
    create_holding,
    delete_holding,
    get_holding,
    get_user_holdings,
    update_holding,
)
from app.users import current_active_user

router = APIRouter(prefix="/api/holdings", tags=["holdings"])


@router.post("", response_model=HoldingRead, status_code=status.HTTP_201_CREATED)
async def create(
    holding_data: HoldingCreate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    return await create_holding(session, user.id, holding_data)


@router.get("", response_model=list[HoldingRead])
async def list_holdings(
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    return await get_user_holdings(session, user.id)


@router.get("/{holding_id}", response_model=HoldingRead)
async def get(
    holding_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    holding = await get_holding(session, holding_id)
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )
    if holding.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )
    return holding


@router.put("/{holding_id}", response_model=HoldingRead)
async def update(
    holding_id: int,
    update_data: HoldingUpdate,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    holding = await get_holding(session, holding_id)
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )
    if holding.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    result = await update_holding(session, holding_id, update_data)
    return result


@router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    holding_id: int,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(current_active_user),
):
    holding = await get_holding(session, holding_id)
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Holding not found"
        )
    if holding.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized"
        )

    await delete_holding(session, holding_id)
