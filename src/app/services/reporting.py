from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movement import MovementType, StockMovementLog
from app.models.product import BinStock, Product
from app.schemas.reports import (
    InventoryValuationReport,
    InventoryWastageReport,
    ProductValuationItem,
    TurnoverMetricItem,
    WastageMetricItem,
)


class ReportingService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_inventory_valuation(self) -> InventoryValuationReport:
        """
        Aggregates physical stock multiplied by product unit cost:
        $$\\text{Valuation} = \\sum (\\text{quantity\\_on\\_hand} \\times \\text{unit\\_cost})$$
        """
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.sku,
                Product.name,
                Product.unit_cost,
                func.coalesce(func.sum(BinStock.quantity_on_hand), 0).label("total_quantity"),
            )
            .outerjoin(BinStock, Product.id == BinStock.product_id)
            .group_by(Product.id, Product.sku, Product.name, Product.unit_cost)
            .order_by(Product.sku)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        breakdown = []
        overall_valuation = Decimal("0.0000")
        overall_units = 0

        for row in rows:
            qty = int(row.total_quantity)
            val = Decimal(qty) * row.unit_cost
            overall_valuation += val
            overall_units += qty
            breakdown.append(
                ProductValuationItem(
                    product_id=row.product_id,
                    sku=row.sku,
                    name=row.name,
                    unit_cost=row.unit_cost,
                    total_quantity_on_hand=qty,
                    total_valuation=val,
                )
            )

        return InventoryValuationReport(
            total_erp_valuation=overall_valuation,
            total_units_on_hand=overall_units,
            breakdown=breakdown,
        )

    async def get_wastage_report(self) -> InventoryWastageReport:
        """Calculates scrap and manual stock write-offs using ADJUSTMENT ledger logs."""
        stmt = (
            select(
                Product.id.label("product_id"),
                Product.sku,
                Product.name,
                Product.unit_cost,
                func.coalesce(func.sum(StockMovementLog.quantity), 0).label("scrapped_units"),
            )
            .join(StockMovementLog, Product.id == StockMovementLog.product_id)
            .where(StockMovementLog.movement_type == MovementType.ADJUSTMENT)
            .group_by(Product.id, Product.sku, Product.name, Product.unit_cost)
        )

        result = await self.session.execute(stmt)
        rows = result.all()

        details = []
        total_loss = Decimal("0.0000")
        total_units = 0

        for row in rows:
            scrapped = int(row.scrapped_units)
            loss = Decimal(scrapped) * row.unit_cost
            total_loss += loss
            total_units += scrapped
            details.append(
                WastageMetricItem(
                    product_id=row.product_id,
                    sku=row.sku,
                    name=row.name,
                    adjusted_units=scrapped,
                    estimated_loss=loss,
                )
            )

        return InventoryWastageReport(
            total_loss_amount=total_loss,
            total_scrapped_units=total_units,
            details=details,
        )

    async def get_stock_turnover(self) -> list[TurnoverMetricItem]:
        """Calculates turnover ratio as total outbound moves divided by average stock on hand."""
        outbound_subq = (
            select(
                StockMovementLog.product_id,
                func.coalesce(func.sum(StockMovementLog.quantity), 0).label("outbound_qty"),
            )
            .where(StockMovementLog.movement_type == MovementType.OUTBOUND)
            .group_by(StockMovementLog.product_id)
            .subquery()
        )

        stmt = (
            select(
                Product.id.label("product_id"),
                Product.sku,
                Product.name,
                func.coalesce(outbound_subq.c.outbound_qty, 0).label("outbound_units"),
                func.coalesce(func.sum(BinStock.quantity_on_hand), 0).label("on_hand_units"),
            )
            .outerjoin(BinStock, Product.id == BinStock.product_id)
            .outerjoin(outbound_subq, Product.id == outbound_subq.c.product_id)
            .group_by(Product.id, Product.sku, Product.name, outbound_subq.c.outbound_qty)
        )

        result = await self.session.execute(stmt)
        records = []
        for row in result.all():
            outbound = int(row.outbound_units)
            on_hand = int(row.on_hand_units)
            ratio = float(outbound / on_hand) if on_hand > 0 else float(outbound)
            records.append(
                TurnoverMetricItem(
                    product_id=row.product_id,
                    sku=row.sku,
                    name=row.name,
                    total_outbound_units=outbound,
                    turnover_ratio=round(ratio, 2),
                )
            )
        return records
