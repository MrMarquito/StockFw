import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.procurement import POStatus, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.product import BinStock, Product


class AutoReplenishmentResult(BaseModel):
    evaluated_products: int
    low_stock_identified: int
    purchase_orders_created: int
    created_po_numbers: List[str]


class AutoReplenishmentService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_replenishment_scan(self) -> AutoReplenishmentResult:
        # Step 1: Query aggregate stock availability per product
        stock_subquery = (
            select(
                BinStock.product_id,
                func.coalesce(
                    func.sum(BinStock.quantity_on_hand - BinStock.allocated_quantity),
                    0,
                ).label("available_stock"),
            )
            .group_by(BinStock.product_id)
            .subquery()
        )

        low_stock_stmt = (
            select(
                Product,
                func.coalesce(stock_subquery.c.available_stock, 0).label("available_units"),
            )
            .outerjoin(stock_subquery, Product.id == stock_subquery.c.product_id)
            .where(func.coalesce(stock_subquery.c.available_stock, 0) <= Product.reorder_threshold)
        )

        result = await self.session.execute(low_stock_stmt)
        low_stock_items = result.all()

        if not low_stock_items:
            return AutoReplenishmentResult(
                evaluated_products=0,
                low_stock_identified=0,
                purchase_orders_created=0,
                created_po_numbers=[],
            )

        # Step 2: Filter out products that already have pending open POs
        active_po_stmt = (
            select(PurchaseOrderItem.product_id)
            .join(PurchaseOrder, PurchaseOrderItem.purchase_order_id == PurchaseOrder.id)
            .where(PurchaseOrder.status.in_([POStatus.DRAFT, POStatus.ORDERED]))
            .distinct()
        )
        active_po_results = await self.session.execute(active_po_stmt)
        products_on_order = set(active_po_results.scalars().all())

        items_to_order: list[tuple[Product, int]] = []
        for prod, available in low_stock_items:
            if prod.id in products_on_order:
                continue

            # Economic order quantity calculation: bring inventory up to 2x threshold + buffer
            order_qty = max((prod.reorder_threshold * 2) - available, 10)
            items_to_order.append((prod, int(order_qty)))

        if not items_to_order:
            return AutoReplenishmentResult(
                evaluated_products=len(low_stock_items),
                low_stock_identified=len(low_stock_items),
                purchase_orders_created=0,
                created_po_numbers=[],
            )

        # Step 3: Map products to appropriate suppliers
        supplier_buckets: dict[uuid.UUID, list[tuple[Product, int]]] = {}

        # Fallback default supplier query
        first_supplier_stmt = select(Supplier.id).limit(1)
        default_supplier_res = await self.session.execute(first_supplier_stmt)
        fallback_supplier_id = default_supplier_res.scalar_one_or_none()

        for prod, qty in items_to_order:
            # Query the vendor used in the latest purchase order for this SKU
            vendor_stmt = (
                select(PurchaseOrder.supplier_id)
                .join(PurchaseOrderItem, PurchaseOrder.id == PurchaseOrderItem.purchase_order_id)
                .where(PurchaseOrderItem.product_id == prod.id)
                .order_by(PurchaseOrder.created_at.desc())
                .limit(1)
            )
            vendor_res = await self.session.execute(vendor_stmt)
            supplier_id = vendor_res.scalar_one_or_none() or fallback_supplier_id

            if not supplier_id:
                continue

            supplier_buckets.setdefault(supplier_id, []).append((prod, qty))

        # Step 4: Generate consolidated DRAFT purchase orders
        created_po_numbers: list[str] = []
        timestamp_slug = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

        for supplier_id, order_entries in supplier_buckets.items():
            po_number = f"AUTO-PO-{timestamp_slug}-{uuid.uuid4().hex[:4].upper()}"
            po = PurchaseOrder(
                po_number=po_number,
                supplier_id=supplier_id,
                status=POStatus.DRAFT,
            )
            for prod, qty in order_entries:
                po.items.append(
                    PurchaseOrderItem(
                        product_id=prod.id,
                        quantity_ordered=qty,
                        unit_price=prod.unit_cost,
                    )
                )

            self.session.add(po)
            created_po_numbers.append(po_number)

        await self.session.commit()

        return AutoReplenishmentResult(
            evaluated_products=len(low_stock_items),
            low_stock_identified=len(low_stock_items),
            purchase_orders_created=len(created_po_numbers),
            created_po_numbers=created_po_numbers,
        )
