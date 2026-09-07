import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.product import BinStock


class Warehouse(Base):
    __tablename__ = "warehouses"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    bins: Mapped[List["BinLocation"]] = relationship(back_populates="warehouse", cascade="all, delete-orphan")


class BinLocation(Base):
    __tablename__ = "bin_locations"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "aisle", "shelf", "bin_code", name="uq_warehouse_coordinate"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    warehouse_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("warehouses.id", ondelete="RESTRICT"), nullable=False)
    zone: Mapped[str] = mapped_column(String(16), nullable=False, default="DEFAULT")
    aisle: Mapped[str] = mapped_column(String(16), nullable=False)
    shelf: Mapped[str] = mapped_column(String(16), nullable=False)
    bin_code: Mapped[str] = mapped_column(String(32), nullable=False)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="bins")
    stocks: Mapped[List["BinStock"]] = relationship(back_populates="bin")
