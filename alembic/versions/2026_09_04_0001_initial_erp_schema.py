"""initial_erp_schema

Revision ID: 2026_09_04_0001
Revises:
Create Date: 2026-09-04 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "2026_09_04_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_warehouses_code", "warehouses", ["code"], unique=True)

    op.create_table(
        "bin_locations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("warehouse_id", sa.UUID(), nullable=False),
        sa.Column("zone", sa.String(length=16), nullable=False),
        sa.Column("aisle", sa.String(length=16), nullable=False),
        sa.Column("shelf", sa.String(length=16), nullable=False),
        sa.Column("bin_code", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["warehouse_id"], ["warehouses.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("warehouse_id", "aisle", "shelf", "bin_code", name="uq_warehouse_coordinate"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("sku", sa.String(length=64), nullable=False),
        sa.Column("upc", sa.String(length=32), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("reorder_threshold", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("unit_cost", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index("ix_products_upc", "products", ["upc"], unique=True)

    op.create_table(
        "bin_stocks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("bin_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("allocated_quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.CheckConstraint("quantity_on_hand >= 0", name="ck_positive_on_hand"),
        sa.CheckConstraint("allocated_quantity >= 0", name="ck_positive_allocated"),
        sa.CheckConstraint("allocated_quantity <= quantity_on_hand", name="ck_allocated_within_bounds"),
        sa.ForeignKeyConstraint(["bin_id"], ["bin_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bin_id", "product_id", name="uq_bin_product"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("contact_email", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )

    op.create_table(
        "purchase_orders",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("po_number", sa.String(length=64), nullable=False),
        sa.Column("supplier_id", sa.UUID(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("DRAFT", "ORDERED", "RECEIVED", "CANCELLED", name="postatus"),
            nullable=False,
            server_default="DRAFT",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_purchase_orders_po_number", "purchase_orders", ["po_number"], unique=True)

    op.create_table(
        "purchase_order_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("purchase_order_id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.CheckConstraint("quantity_ordered > 0", name="ck_positive_po_quantity"),
        sa.CheckConstraint("unit_price >= 0", name="ck_positive_unit_price"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["purchase_order_id"], ["purchase_orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "stock_movement_logs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("product_id", sa.UUID(), nullable=False),
        sa.Column("source_bin_id", sa.UUID(), nullable=True),
        sa.Column("target_bin_id", sa.UUID(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column(
            "movement_type",
            sa.Enum("INBOUND", "OUTBOUND", "TRANSFER", "ADJUSTMENT", name="movementtype"),
            nullable=False,
        ),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("quantity > 0", name="ck_movement_log_quantity_positive"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["source_bin_id"], ["bin_locations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_bin_id"], ["bin_locations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stock_movement_product_timestamp", "stock_movement_logs", ["product_id", "timestamp"])


def downgrade() -> None:
    op.drop_index("ix_stock_movement_product_timestamp", table_name="stock_movement_logs")
    op.drop_table("stock_movement_logs")
    op.drop_table("purchase_order_items")
    op.drop_index("ix_purchase_orders_po_number", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_table("suppliers")
    op.drop_table("bin_stocks")
    op.drop_index("ix_products_upc", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
    op.drop_table("bin_locations")
    op.drop_index("ix_warehouses_code", table_name="warehouses")
    op.drop_table("warehouses")
    sa.Enum(name="movementtype").drop(op.get_bind(), checkfirst=False)
    sa.Enum(name="postatus").drop(op.get_bind(), checkfirst=False)
