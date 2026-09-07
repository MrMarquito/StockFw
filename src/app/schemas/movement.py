import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.movement import MovementType


class StockMovementRead(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    source_bin_id: Optional[uuid.UUID]
    target_bin_id: Optional[uuid.UUID]
    quantity: int
    movement_type: MovementType
    user_id: uuid.UUID
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)
