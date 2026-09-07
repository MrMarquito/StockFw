import uuid
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.warehouse import BinLocation


class Product(Base):
    __tablename__ = "products"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    upc: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    reorder_threshold: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    stocks: Mapped[List["BinStock"]] = relationship(back_populates="product")


class BinStock(Base):
    __tablename__ = "bin_stocks"
    __table_args__ = (
        UniqueConstraint("bin_id", "product_id", name="uq_bin_product"),
        CheckConstraint("quantity_on_hand >= 0", name="ck_positive_on_hand"),
        CheckConstraint("allocated_quantity >= 0", name="ck_positive_allocated"),
        CheckConstraint("allocated_quantity <= quantity_on_hand", name="ck_allocated_within_bounds"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bin_locations.id", ondelete="RESTRICT"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    allocated_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    bin: Mapped["BinLocation"] = relationship(back_populates="stocks")
    product: Mapped["Product"] = relationship(back_populates="stocks")
