import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.movement import MovementType, StockMovementLog
from app.models.product import BinStock, Product
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_reporting_valuation_and_wastage(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["inventory:read", "admin"])
    headers = {"Authorization": f"Bearer {token}"}

    # Setup Warehouse & Bin
    wh = Warehouse(code=f"WH-REP-{uuid.uuid4().hex[:6]}", name="Valuation WH")
    session.add(wh)
    await session.flush()

    bin_loc = BinLocation(warehouse_id=wh.id, zone="A", aisle="01", shelf="1", bin_code="V-01-A")
    prod1 = Product(sku=f"SKU-V1-{uuid.uuid4().hex[:6]}", name="Item A", unit_cost=Decimal("10.0000"))
    prod2 = Product(sku=f"SKU-V2-{uuid.uuid4().hex[:6]}", name="Item B", unit_cost=Decimal("25.5000"))
    session.add_all([bin_loc, prod1, prod2])
    await session.flush()

    # Bin stocks: 10 units of Item A ($100), 4 units of Item B ($102)
    stock1 = BinStock(bin_id=bin_loc.id, product_id=prod1.id, quantity_on_hand=10, allocated_quantity=0)
    stock2 = BinStock(bin_id=bin_loc.id, product_id=prod2.id, quantity_on_hand=4, allocated_quantity=0)
    
    # Wastage log: 2 units of Item A written off
    waste_log = StockMovementLog(
        product_id=prod1.id,
        source_bin_id=bin_loc.id,
        target_bin_id=None,
        quantity=2,
        movement_type=MovementType.ADJUSTMENT,
        user_id=user_id,
    )
    session.add_all([stock1, stock2, waste_log])
    await session.commit()

    # Query Valuation Endpoint
    val_resp = await client.get("/api/v1/reports/valuation", headers=headers)
    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert float(val_data["total_erp_valuation"]) >= 202.0
    assert val_data["total_units_on_hand"] >= 14

    # Query Wastage Endpoint
    waste_resp = await client.get("/api/v1/reports/wastage", headers=headers)
    assert waste_resp.status_code == 200
    waste_data = waste_resp.json()
    assert waste_data["total_scrapped_units"] >= 2
    assert float(waste_data["total_loss_amount"]) >= 20.0
