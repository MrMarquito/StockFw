from fastapi import APIRouter, Query, Security

from app.api.deps import CurrentUser, DBSession, get_current_user
from app.schemas.anomaly import AnomalyDetectionReport
from app.services.anomaly_detector import AnomalyDetectionService

router = APIRouter()


@router.get("/anomalies", response_model=AnomalyDetectionReport)
async def scan_inventory_anomalies(
    db: DBSession,
    contamination: float = Query(0.05, ge=0.01, le=0.5),
    min_samples: int = Query(10, ge=5),
    _: CurrentUser = Security(get_current_user, scopes=["admin"]),
):
    service = AnomalyDetectionService(db)
    return await service.detect_anomalies(
        contamination=contamination,
        min_samples=min_samples,
    )
