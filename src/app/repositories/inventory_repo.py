import uuid
from typing import Optional, Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import BinStock
from app.models.movement import MovementType, StockMovementLog
from app.repositories.base import BaseRepository


class InventoryRepository(BaseRepository[BinStock]):
    def __init__(self, session: AsyncSession):
        super().__init__(BinStock, session)

    async def get_bin_stock_for_update(self, bin_id: uuid.UUID, product_id: uuid.UUID) -> Optional[BinStock]:
        """Pessimistically lock the specific bin-stock row using SELECT ... FOR UPDATE."""
        stmt = (
            select(BinStock)
            .where(BinStock.bin_id == bin_id, BinStock.product_id == product_id)
            .with_for_update()
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_or_create_bin_stock_for_update(self, bin_id: uuid.UUID, product_id: uuid.UUID) -> BinStock:
        stock = await self.get_bin_stock_for_update(bin_id, product_id)
        if not stock:
            stock = BinStock(
                bin_id=bin_id,
                product_id=product_id,
                quantity_on_hand=0,
                allocated_quantity=0,
            )
            self.session.add(stock)
            await self.session.flush()
        return stock

    def log_movement(
        self,
        product_id: uuid.UUID,
        source_bin_id: Optional[uuid.UUID],
        target_bin_id: Optional[uuid.UUID],
        quantity: int,
        movement_type: MovementType,
        user_id: uuid.UUID,
    ) -> StockMovementLog:
        log_entry = StockMovementLog(
            product_id=product_id,
            source_bin_id=source_bin_id,
            target_bin_id=target_bin_id,
            quantity=quantity,
            movement_type=movement_type,
            user_id=user_id,
        )
        self.session.add(log_entry)
        return log_entry

    async def get_movements_by_product(
        self, product_id: uuid.UUID, limit: int = 100
    ) -> Sequence[StockMovementLog]:
        stmt = (
            select(StockMovementLog)
            .where(StockMovementLog.product_id == product_id)
            .order_by(StockMovementLog.timestamp.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
