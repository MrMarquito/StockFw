import uuid
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.product import Product
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_create_and_read_product(client: AsyncClient, session: AsyncSession):
    token = create_access_token(
        subject=uuid.uuid4(),
        scopes=["admin", "inventory:read"],
    )
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "name": "Industrial Widget",
        "reorder_threshold": 15,
        "unit_cost": "24.5000",
    }
    response = await client.post("/api/v1/inventory/products", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == payload["sku"]
    assert float(data["unit_cost"]) == 24.5
