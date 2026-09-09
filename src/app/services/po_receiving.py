import uuid
from typing import List
from fastapi import HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.movement import MovementType
from app.models.procurement import POStatus, PurchaseOrder
from app.repositories.inventory_repo import InventoryRepository


class POReceiveItemPayload(BaseModel):
    product_id: uuid.UUID
    target_bin_id: uuid.UUID
    quantity_received: int = Field(..., gt=0)


class POReceiveRequest(BaseModel):
    items: List[POReceiveItemPayload]


class POReceivingService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory_repo = InventoryRepository(session)

    async def transition_to_ordered(self, po_id: uuid.UUID) -> PurchaseOrder:
        stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id).with_for_update()
        result = await self.session.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        if po.status != POStatus.DRAFT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot order a PO in '{po.status.value}' state. Must be in DRAFT.",
            )

        po.status = POStatus.ORDERED
        await self.session.commit()
        await self.session.refresh(po)
        return po

    async def receive_purchase_order(
        self,
        po_id: uuid.UUID,
        receive_items: List[POReceiveItemPayload],
        user_id: uuid.UUID,
    ) -> PurchaseOrder:
        stmt = (
            select(PurchaseOrder)
            .where(PurchaseOrder.id == po_id)
            .options(selectinload(PurchaseOrder.items))
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        po = result.scalar_one_or_none()

        if not po:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase order not found")
        if po.status != POStatus.ORDERED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Only purchase orders in 'ORDERED' status can be received (current status: '{po.status.value}')",
            )

        ordered_quantities: dict[uuid.UUID, int] = {item.product_id: item.quantity_ordered for item in po.items}
        
        # Aggregate received quantities across bins per product
        receiving_totals: dict[uuid.UUID, int] = {}
        for item in receive_items:
            if item.product_id not in ordered_quantities:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {item.product_id} is not part of Purchase Order {po.po_number}",
                )
            receiving_totals[item.product_id] = receiving_totals.get(item.product_id, 0) + item.quantity_received

        for prod_id, total_received in receiving_totals.items():
            if total_received > ordered_quantities[prod_id]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Total received quantity ({total_received}) exceeds ordered amount ({ordered_quantities[prod_id]}) for product {prod_id}",
                )

        # Sort allocations by target_bin_id to prevent concurrent deadlock during multi-bin putaway
        sorted_allocations = sorted(receive_items, key=lambda x: x.target_bin_id)

        for alloc in sorted_allocations:
            stock = await self.inventory_repo.get_or_create_bin_stock_for_update(
                bin_id=alloc.target_bin_id,
                product_id=alloc.product_id,
            )
            stock.quantity_on_hand += alloc.quantity_received

            self.inventory_repo.log_movement(
                product_id=alloc.product_id,
                source_bin_id=None,
                target_bin_id=alloc.target_bin_id,
                quantity=alloc.quantity_received,
                movement_type=MovementType.INBOUND,
                user_id=user_id,
            )

        po.status = POStatus.RECEIVED
        await self.session.commit()
        await self.session.refresh(po)
        return po
