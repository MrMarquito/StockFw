import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.movement import MovementType, StockMovementLog
from app.models.product import BinStock, Product
from app.models.procurement import Supplier
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_purchase_order_full_receiving_lifecycle(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["po:read", "po:write", "inventory:read"])
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Warehouse, Bin, Product, and Supplier
    wh = Warehouse(code=f"WH-RCV-{uuid.uuid4().hex[:6]}", name="Receiving Hub")
    session.add(wh)
    await session.flush()

    bin_loc = BinLocation(warehouse_id=wh.id, zone="IN", aisle="01", shelf="A", bin_code="IN-01-A")
    prod = Product(sku=f"SKU-RCV-{uuid.uuid4().hex[:6]}", name="Valves", unit_cost=Decimal("45.00"))
    supplier = Supplier(name=f"Vendor-{uuid.uuid4().hex[:6]}", contact_email="vendor@example.com")
    session.add_all([bin_loc, prod, supplier])
    await session.commit()

    # Step 1: Create PO in DRAFT status
    po_payload = {
        "po_number": f"PO-{uuid.uuid4().hex[:8].upper()}",
        "supplier_id": str(supplier.id),
        "items": [
            {
                "product_id": str(prod.id),
                "quantity_ordered": 50,
                "unit_price": "45.00",
            }
        ],
    }
    po_resp = await client.post("/api/v1/procurement/", json=po_payload, headers=headers)
    assert po_resp.status_code == 201
    po_data = po_resp.json()
    po_id = po_data["id"]
    assert po_data["status"] == "DRAFT"

    # Step 2: Attempt to receive directly from DRAFT (must fail with 400)
    receive_payload = {
        "items": [
            {
                "product_id": str(prod.id),
                "target_bin_id": str(bin_loc.id),
                "quantity_received": 50,
            }
        ]
    }
    fail_rx = await client.post(f"/api/v1/procurement/{po_id}/receive", json=receive_payload, headers=headers)
    assert fail_rx.status_code == 400

    # Step 3: Transition PO from DRAFT to ORDERED
    order_resp = await client.post(f"/api/v1/procurement/{po_id}/order", headers=headers)
    assert order_resp.status_code == 200
    assert order_resp.json()["status"] == "ORDERED"

    # Step 4: Receive PO into target bin
    rx_resp = await client.post(f"/api/v1/procurement/{po_id}/receive", json=receive_payload, headers=headers)
    assert rx_resp.status_code == 200
    assert rx_resp.json()["status"] == "RECEIVED"

    # Step 5: Verify bin balance is updated in the database
    stock_stmt = select(BinStock).where(BinStock.bin_id == bin_loc.id, BinStock.product_id == prod.id)
    stock_res = await session.execute(stock_stmt)
    stock = stock_res.scalar_one_or_none()
    assert stock is not None
    assert stock.quantity_on_hand == 50

    # Step 6: Verify immutable INBOUND movement log was generated
    log_stmt = select(StockMovementLog).where(
        StockMovementLog.product_id == prod.id,
        StockMovementLog.target_bin_id == bin_loc.id,
    )
    log_res = await session.execute(log_stmt)
    movement = log_res.scalar_one_or_none()
    assert movement is not None
    assert movement.movement_type == MovementType.INBOUND
    assert movement.quantity == 50
    assert movement.source_bin_id is None
    assert movement.user_id == user_id
