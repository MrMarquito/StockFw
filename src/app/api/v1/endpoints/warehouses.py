from typing import Sequence
from fastapi import APIRouter, Security, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, get_current_user
from app.models.warehouse import BinLocation, Warehouse
from app.schemas.warehouse import (
    BinLocationCreate,
    BinLocationRead,
    WarehouseCreate,
    WarehouseRead,
)

router = APIRouter()


@router.post("/", response_model=WarehouseRead, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehouseCreate,
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["admin"]),
):
    warehouse = Warehouse(**payload.model_dump())
    db.add(warehouse)
    await db.commit()
    await db.refresh(warehouse)
    return warehouse


@router.get("/", response_model=Sequence[WarehouseRead])
async def list_warehouses(
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["inventory:read"]),
):
    result = await db.execute(select(Warehouse))
    return result.scalars().all()


@router.post("/bins", response_model=BinLocationRead, status_code=status.HTTP_201_CREATED)
async def create_bin_location(
    payload: BinLocationCreate,
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["admin"]),
):
    bin_location = BinLocation(**payload.model_dump())
    db.add(bin_location)
    await db.commit()
    await db.refresh(bin_location)
    return bin_location
