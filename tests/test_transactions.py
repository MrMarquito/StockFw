import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.product import BinStock, Product
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_atomic_stock_transfer_success(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["inventory:write", "inventory:read"])
    headers = {"Authorization": f"Bearer {token}"}

    # Setup domain records
    wh = Warehouse(code=f"WH-{uuid.uuid4().hex[:6]}", name="Main WH")
    session.add(wh)
    await session.flush()

    bin1 = BinLocation(warehouse_id=wh.id, zone="A", aisle="01", shelf="1", bin_code="A-01-1-A")
    bin2 = BinLocation(warehouse_id=wh.id, zone="A", aisle="01", shelf="1", bin_code="A-01-1-B")
    prod = Product(sku=f"SKU-{uuid.uuid4().hex[:6]}", name="Bearing", unit_cost=Decimal("10.00"))
    session.add_all([bin1, bin2, prod])
    await session.flush()

    # Source stock has 100 units
    stock1 = BinStock(bin_id=bin1.id, product_id=prod.id, quantity_on_hand=100, allocated_quantity=0)
    session.add(stock1)
    await session.commit()

    payload = {
        "product_id": str(prod.id),
        "source_bin_id": str(bin1.id),
        "target_bin_id": str(bin2.id),
        "quantity": 35,
    }
    res = await client.post("/api/v1/inventory/transfer", json=payload, headers=headers)
    assert res.status_code == 200

    # Query balances post-transfer
    stocks_res = await client.get(f"/api/v1/inventory/stocks?product_id={prod.id}", headers=headers)
    stocks = {item["bin_id"]: item["quantity_on_hand"] for item in stocks_res.json()}

    assert stocks[str(bin1.id)] == 65
    assert stocks[str(bin2.id)] == 35


@pytest.mark.asyncio
async def test_atomic_stock_transfer_insufficient_stock(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["inventory:write", "inventory:read"])
    headers = {"Authorization": f"Bearer {token}"}

    wh = Warehouse(code=f"WH-{uuid.uuid4().hex[:6]}", name="Secondary WH")
    session.add(wh)
    await session.flush()

    bin1 = BinLocation(warehouse_id=wh.id, zone="B", aisle="02", shelf="1", bin_code="B-02-1-A")
    bin2 = BinLocation(warehouse_id=wh.id, zone="B", aisle="02", shelf="1", bin_code="B-02-1-B")
    prod = Product(sku=f"SKU-{uuid.uuid4().hex[:6]}", name="Gasket", unit_cost=Decimal("5.00"))
    session.add_all([bin1, bin2, prod])
    await session.flush()

    stock1 = BinStock(bin_id=bin1.id, product_id=prod.id, quantity_on_hand=10, allocated_quantity=5)
    session.add(stock1)
    await session.commit()

    payload = {
        "product_id": str(prod.id),
        "source_bin_id": str(bin1.id),
        "target_bin_id": str(bin2.id),
        "quantity": 10,  # Only 5 unallocated available
    }
    res = await client.post("/api/v1/inventory/transfer", json=payload, headers=headers)
    assert res.status_code == 409
