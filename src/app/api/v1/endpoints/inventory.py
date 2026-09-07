import uuid
from typing import Sequence
from fastapi import APIRouter, HTTPException, Security, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DBSession, get_current_user
from app.models.product import BinStock, Product
from app.schemas.inventory import (
    BinStockRead,
    ProductCreate,
    ProductRead,
    StockTransferRequest,
)
from app.schemas.movement import StockMovementRead
from app.services.stock_transfer import StockTransferService

router = APIRouter()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    payload: ProductCreate,
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["admin"]),
):
    product = Product(**payload.model_dump())
    db.add(product)
    await db.commit()
    await db.refresh(product)
    return product


@router.get("/stocks", response_model=Sequence[BinStockRead])
async def list_bin_stocks(
    db: DBSession,
    product_id: uuid.UUID | None = None,
    _: CurrentUser = Security(get_current_user, scopes=["inventory:read"]),
):
    stmt = select(BinStock)
    if product_id:
        stmt = stmt.where(BinStock.product_id == product_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/transfer", response_model=StockMovementRead, status_code=status.HTTP_200_OK)
async def transfer_stock(
    payload: StockTransferRequest,
    db: DBSession,
    current_user: CurrentUser = Security(get_current_user, scopes=["inventory:write"]),
):
    service = StockTransferService(db)
    movement = await service.transfer_stock(
        product_id=payload.product_id,
        source_bin_id=payload.source_bin_id,
        target_bin_id=payload.target_bin_id,
        quantity=payload.quantity,
        user_id=current_user.id,
    )
    return movement
