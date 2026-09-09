from typing import List
from fastapi import APIRouter, Security

from app.api.deps import CurrentUser, DBSession, get_current_user
from app.schemas.reports import (
    InventoryValuationReport,
    InventoryWastageReport,
    TurnoverMetricItem,
)
from app.services.reporting import ReportingService

router = APIRouter()


@router.get("/valuation", response_model=InventoryValuationReport)
async def get_inventory_valuation(
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["inventory:read"]),
):
    service = ReportingService(db)
    return await service.get_inventory_valuation()


@router.get("/wastage", response_model=InventoryWastageReport)
async def get_inventory_wastage(
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["inventory:read"]),
):
    service = ReportingService(db)
    return await service.get_wastage_report()


@router.get("/turnover", response_model=List[TurnoverMetricItem])
async def get_stock_turnover(
    db: DBSession,
    _: CurrentUser = Security(get_current_user, scopes=["inventory:read"]),
):
    service = ReportingService(db)
    return await service.get_stock_turnover()
