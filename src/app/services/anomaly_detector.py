import numpy as np
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.movement import MovementType, StockMovementLog
from app.schemas.anomaly import AnomalyDetectionReport, AnomalyRecord


class AnomalyDetectionService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_anomalies(
        self,
        contamination: float = 0.05,
        min_samples: int = 10,
    ) -> AnomalyDetectionReport:
        stmt = select(StockMovementLog).order_by(StockMovementLog.timestamp.desc())
        result = await self.session.execute(stmt)
        movements = list(result.scalars().all())

        if len(movements) < min_samples:
            return AnomalyDetectionReport(
                total_records_analyzed=len(movements),
                anomalies_detected=0,
                flagged_movements=[],
            )

        # Feature matrix extraction:
        # 1. quantity: Volume of inventory altered
        # 2. hour: Operational time of day (0-23)
        # 3. is_weekend: Binary flag (1 if Sat/Sun else 0)
        # 4. is_adjustment: Flag write-offs and scrap operations heavily
        features = []
        for m in movements:
            hour = m.timestamp.hour
            is_weekend = 1.0 if m.timestamp.weekday() >= 5 else 0.0
            is_adj = 1.0 if m.movement_type == MovementType.ADJUSTMENT else 0.0
            features.append([float(m.quantity), float(hour), is_weekend, is_adj])

        x_data = np.array(features)

        model = IsolationForest(
            contamination=contamination,
            random_state=42,
            n_estimators=100,
        )
        predictions = model.fit_predict(x_data)  # -1 for anomaly, 1 for inlier
        scores = model.decision_function(x_data)  # Lower values indicate severe anomalies

        flagged: list[AnomalyRecord] = []
        for idx, (m, pred, score) in enumerate(zip(movements, predictions, scores)):
            if pred == -1:
                flagged.append(
                    AnomalyRecord(
                        movement_id=m.id,
                        product_id=m.product_id,
                        movement_type=m.movement_type,
                        quantity=m.quantity,
                        timestamp=m.timestamp,
                        user_id=m.user_id,
                        anomaly_score=float(score),
                        is_anomaly=True,
                    )
                )

        return AnomalyDetectionReport(
            total_records_analyzed=len(movements),
            anomalies_detected=len(flagged),
            flagged_movements=flagged,
        )
