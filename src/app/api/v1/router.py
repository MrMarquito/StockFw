from fastapi import APIRouter
from app.api.v1.endpoints import auth, audit, inventory, purchase_orders, reports, warehouses

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(purchase_orders.router, prefix="/procurement", tags=["procurement"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
