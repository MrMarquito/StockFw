import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movement import MovementType, StockMovementLog
from app.repositories.inventory_repo import InventoryRepository


class StockTransferService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.inventory_repo = InventoryRepository(session)

    async def transfer_stock(
        self,
        product_id: uuid.UUID,
        source_bin_id: uuid.UUID,
        target_bin_id: uuid.UUID,
        quantity: int,
        user_id: uuid.UUID,
    ) -> StockMovementLog:
        if source_bin_id == target_bin_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Source and target bins must be distinct",
            )
        if quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transfer quantity must be positive",
            )

        # Deterministic locking order prevents deadlocks during concurrent reverse transfers
        first_bin, second_bin = sorted([source_bin_id, target_bin_id])

        if first_bin == source_bin_id:
            source_stock = await self.inventory_repo.get_bin_stock_for_update(source_bin_id, product_id)
            target_stock = await self.inventory_repo.get_or_create_bin_stock_for_update(target_bin_id, product_id)
        else:
            target_stock = await self.inventory_repo.get_or_create_bin_stock_for_update(target_bin_id, product_id)
            source_stock = await self.inventory_repo.get_bin_stock_for_update(source_bin_id, product_id)

        if not source_stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Source stock record does not exist",
            )

        available_quantity = source_stock.quantity_on_hand - source_stock.allocated_quantity
        if available_quantity < quantity:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Insufficient unallocated stock: {available_quantity} available, {quantity} requested",
            )

        # Mutate records within transaction
        source_stock.quantity_on_hand -= quantity
        target_stock.quantity_on_hand += quantity

        movement_log = self.inventory_repo.log_movement(
            product_id=product_id,
            source_bin_id=source_bin_id,
            target_bin_id=target_bin_id,
            quantity=quantity,
            movement_type=MovementType.TRANSFER,
            user_id=user_id,
        )

        await self.session.commit()
        await self.session.refresh(movement_log)
        return movement_log
