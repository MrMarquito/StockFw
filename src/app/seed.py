import asyncio
import uuid
from decimal import Decimal
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.movement import MovementType, StockMovementLog
from app.models.procurement import POStatus, PurchaseOrder, PurchaseOrderItem, Supplier
from app.models.product import BinStock, Product
from app.models.warehouse import BinLocation, Warehouse

SYSTEM_USER_ID = uuid.UUID("a0000000-0000-0000-0000-000000000001")


async def seed_database() -> None:
    async with async_session_factory() as session:
        # Check if baseline data already exists
        existing_wh = await session.execute(select(Warehouse).filter_by(code="WH-NORTH"))
        if existing_wh.scalar_one_or_none():
            print("\n[!] Database already contains seed records. Skipping creation.")
            return

        print("\n--- Seeding Warehouse ERP Database ---")

        # 1. Warehouse Hierarchy
        warehouse = Warehouse(code="WH-NORTH", name="Northern Distribution Hub")
        session.add(warehouse)
        await session.flush()

        source_bin = BinLocation(
            warehouse_id=warehouse.id,
            zone="A",
            aisle="01",
            shelf="1",
            bin_code="BIN-A-01-A",
        )
        target_bin = BinLocation(
            warehouse_id=warehouse.id,
            zone="B",
            aisle="02",
            shelf="1",
            bin_code="BIN-B-02-B",
        )
        session.add_all([source_bin, target_bin])
        await session.flush()

        # 2. Product Catalog & Supplier
        supplier = Supplier(
            name="Apex Industrial Supply Co.",
            contact_email="dispatch@apexsupply.io",
        )
        product = Product(
            sku="SKU-BRG-100",
            name="Precision Heavy Bearings (Pack of 10)",
            reorder_threshold=15,
            unit_cost=Decimal("24.5000"),
        )
        session.add_all([supplier, product])
        await session.flush()

        # 3. Initial Inventory Balance
        stock_entry = BinStock(
            bin_id=source_bin.id,
            product_id=product.id,
            quantity_on_hand=150,
            allocated_quantity=0,
        )
        session.add(stock_entry)

        # 4. Inbound Movement Audit Trail
        movement = StockMovementLog(
            product_id=product.id,
            source_bin_id=None,
            target_bin_id=source_bin.id,
            quantity=150,
            movement_type=MovementType.INBOUND,
            user_id=SYSTEM_USER_ID,
        )
        session.add(movement)

        await session.commit()

        print("\n=== Copy-Paste Testing Identifiers ===")
        print(f"Product SKU:        {product.sku} ({product.name})")
        print(f"Product UUID:       {product.id}")
        print(f"Source Bin UUID:    {source_bin.id}  [{source_bin.bin_code}]")
        print(f"Target Bin UUID:    {target_bin.id}  [{target_bin.bin_code}]")
        print(f"Starting Stock:     150 units in {source_bin.bin_code}")
        print("=======================================\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
