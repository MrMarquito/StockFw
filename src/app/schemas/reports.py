import uuid
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict


class ProductValuationItem(BaseModel):
    product_id: uuid.UUID
    sku: str
    name: str
    unit_cost: Decimal
    total_quantity_on_hand: int
    total_valuation: Decimal
    model_config = ConfigDict(from_attributes=True)


class InventoryValuationReport(BaseModel):
    total_erp_valuation: Decimal
    total_units_on_hand: int
    breakdown: List[ProductValuationItem]


class WastageMetricItem(BaseModel):
    product_id: uuid.UUID
    sku: str
    name: str
    adjusted_units: int
    estimated_loss: Decimal


class InventoryWastageReport(BaseModel):
    total_loss_amount: Decimal
    total_scrapped_units: int
    details: List[WastageMetricItem]


class TurnoverMetricItem(BaseModel):
    product_id: uuid.UUID
    sku: str
    name: str
    total_outbound_units: int
    turnover_ratio: float
