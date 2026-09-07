import enum
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MovementType(str, enum.Enum):
    INBOUND = "INBOUND"
    OUTBOUND = "OUTBOUND"
    TRANSFER = "TRANSFER"
    ADJUSTMENT = "ADJUSTMENT"


class StockMovementLog(Base):
    __tablename__ = "stock_movement_logs"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_movement_log_quantity_positive"),
        Index("ix_stock_movement_product_timestamp", "product_id", "timestamp"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), nullable=False)
    source_bin_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bin_locations.id", ondelete="RESTRICT"), nullable=True)
    target_bin_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("bin_locations.id", ondelete="RESTRICT"), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    movement_type: Mapped[MovementType] = mapped_column(Enum(MovementType), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )
