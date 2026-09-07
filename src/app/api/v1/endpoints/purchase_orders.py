import uuid
from decimal import Decimal
from typing import List, Sequence
from fastapi import APIRouter, HTTPException, Security, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser, DBSession, get_current_user
from app.models.procurement import POStatus, PurchaseOrder, PurchaseOrderItem
from app.repositories.order_repo import OrderRepository

router = APIRouter()


class POItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity_ordered: int
    unit_price: Decimal


class POCreate(BaseModel):
    po_number: str
    supplier_id: uuid.UUID
    items: List[POItemCreate]


class POItemRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    quantity_ordered: int
    unit_price: Decimal


class PORead(BaseModel):
    id: uuid.UUID
    po_number: str
    supplier_id: uuid.UUID
    status: POStatus
    items: List[POItemRead]


@router.post("/", response_model=PORead, status_code=status.HTTP_201_CREATED)
async def create_purchase_order(
    payload: POCreate,
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["po:write"]),
):
    po = PurchaseOrder(po_number=payload.po_number, supplier_id=payload.supplier_id)
    for item in payload.items:
        po.items.append(
            PurchaseOrderItem(
                product_id=item.product_id,
                quantity_ordered=item.quantity_ordered,
                unit_price=item.unit_price,
            )
        )
    db.add(po)
    await db.commit()
    repo = OrderRepository(db)
    return await repo.get_with_items(po.id)


@router.get("/{po_id}", response_model=PORead)
async def get_purchase_order(
    po_id: uuid.UUID,
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["po:read"]),
):
    repo = OrderRepository(db)
    po = await repo.get_with_items(po_id)
    if not po:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
    return po
