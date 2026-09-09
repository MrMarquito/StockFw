import uuid
from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

from app.models.movement import MovementType


class AnomalyRecord(BaseModel):
    movement_id: uuid.UUID
    product_id: uuid.UUID
    movement_type: MovementType
    quantity: int
    timestamp: datetime
    user_id: uuid.UUID
    anomaly_score: float
    is_anomaly: bool
    model_config = ConfigDict(from_attributes=True)


class AnomalyDetectionReport(BaseModel):
    total_records_analyzed: int
    anomalies_detected: int
    flagged_movements: List[AnomalyRecord]
