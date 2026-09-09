import uuid
from datetime import datetime, timezone
from decimal import Decimal
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.movement import MovementType, StockMovementLog
from app.models.product import Product
from app.models.warehouse import BinLocation, Warehouse


@pytest.mark.asyncio
async def test_isolation_forest_flags_shrinkage_outlier(client: AsyncClient, session: AsyncSession):
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, scopes=["admin", "inventory:read"])
    headers = {"Authorization": f"Bearer {token}"}

    wh = Warehouse(code=f"WH-ML-{uuid.uuid4().hex[:6]}", name="Audit Hub")
    session.add(wh)
    await session.flush()

    bin_loc = BinLocation(warehouse_id=wh.id, zone="M", aisle="01", shelf="1", bin_code="M-01-A")
    prod = Product(sku=f"SKU-ML-{uuid.uuid4().hex[:6]}", name="Copper Wire", unit_cost=Decimal("12.00"))
    session.add_all([bin_loc, prod])
    await session.commit()

    # Generate 15 normal daytime transactions (Weekdays, 10:00 - 15:00, small quantities)
    for i in range(15):
        normal_log = StockMovementLog(
            product_id=prod.id,
            source_bin_id=bin_loc.id,
            target_bin_id=None,
            quantity=10 + (i % 3),
            movement_type=MovementType.OUTBOUND,
            user_id=user_id,
            timestamp=datetime(2026, 9, 2, 10 + (i % 5), 30, 0, tzinfo=timezone.utc),  # Wednesday
        )
        session.add(normal_log)

    # Inject 1 high-variance outlier: Massive scrap adjustment at 3:00 AM on Sunday
    outlier_log = StockMovementLog(
        product_id=prod.id,
        source_bin_id=bin_loc.id,
        target_bin_id=None,
        quantity=9500,
        movement_type=MovementType.ADJUSTMENT,
        user_id=user_id,
        timestamp=datetime(2026, 9, 6, 3, 15, 0, tzinfo=timezone.utc),  # Sunday morning
    )
    session.add(outlier_log)
    await session.commit()

    response = await client.get("/api/v1/audit/anomalies?contamination=0.1&min_samples=10", headers=headers)
    assert response.status_code == 200

    data = response.json()
    assert data["total_records_analyzed"] >= 16
    assert data["anomalies_detected"] >= 1

    flagged_ids = [item["movement_id"] for item in data["flagged_movements"]]
    assert str(outlier_log.id) in flagged_ids
