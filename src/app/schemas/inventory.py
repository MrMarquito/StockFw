import uuid
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    sku: str = Field(..., max_length=64)
    upc: Optional[str] = Field(None, max_length=32)
    name: str = Field(..., max_length=255)
    reorder_threshold: int = Field(default=10, ge=0)
    unit_cost: Decimal = Field(..., ge=0)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: uuid.UUID
    model_config = ConfigDict(from_attributes=True)


class BinStockRead(BaseModel):
    id: uuid.UUID
    bin_id: uuid.UUID
    product_id: uuid.UUID
    quantity_on_hand: int
    allocated_quantity: int
    model_config = ConfigDict(from_attributes=True)


class StockTransferRequest(BaseModel):
    product_id: uuid.UUID
    source_bin_id: uuid.UUID
    target_bin_id: uuid.UUID
    quantity: int = Field(..., gt=0)
