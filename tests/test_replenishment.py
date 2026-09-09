import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.procurement import POStatus, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.product import BinStock, Product
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_auto_replenishment_generates_draft_po(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["po:write"])
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Warehouse, Bin, Supplier, and Low-Stock Product
    wh = Warehouse(code=f"WH-AUTO-{uuid.uuid4().hex[:6]}", name="Auto WH")
    session.add(wh)
    await session.flush()

    bin_loc = BinLocation(warehouse_id=wh.id, zone="R", aisle="01", shelf="1", bin_code="R-01-A")
    supplier = Supplier(name=f"Supplier-{uuid.uuid4().hex[:6]}", contact_email="vendor@auto.com")
    prod = Product(
        sku=f"SKU-LOW-{uuid.uuid4().hex[:6]}",
        name="Ball Bearing",
        unit_cost=Decimal("15.0000"),
        reorder_threshold=20,  # Threshold = 20
    )
    session.add_all([bin_loc, supplier, prod])
    await session.flush()

    # Seed historical received PO to establish vendor association for this SKU
    historical_po = PurchaseOrder(
        po_number=f"HIST-{uuid.uuid4().hex[:8].upper()}",
        supplier_id=supplier.id,
        status=POStatus.RECEIVED,
    )
    historical_po.items.append(
        PurchaseOrderItem(
            product_id=prod.id,
            quantity_ordered=50,
            unit_price=prod.unit_cost,
        )
    )
    session.add(historical_po)

    # Stock is 5 (strictly below threshold of 20)
    stock = BinStock(bin_id=bin_loc.id, product_id=prod.id, quantity_on_hand=5, allocated_quantity=0)
    session.add(stock)
    await session.commit()

    # Step 1: Trigger auto replenishment
    response = await client.post("/api/v1/procurement/auto-replenish", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert data["purchase_orders_created"] == 1
    assert len(data["created_po_numbers"]) == 1

    created_po_number = data["created_po_numbers"][0]

    # Verify PO in database
    po_stmt = select(PurchaseOrder).where(PurchaseOrder.po_number == created_po_number)
    po_res = await session.execute(po_stmt)
    po = po_res.scalar_one()

    assert po.status == POStatus.DRAFT
    assert po.supplier_id == supplier.id

    # Step 2: Re-running replenishment must NOT generate duplicate orders for the same SKU
    second_run = await client.post("/api/v1/procurement/auto-replenish", headers=headers)
    assert second_run.status_code == 200
    assert second_run.json()["purchase_orders_created"] == 0
