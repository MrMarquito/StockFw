from fastapi import APIRouter
from app.api.v1.endpoints import auth, inventory, purchase_orders, warehouses

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(warehouses.router, prefix="/warehouses", tags=["warehouses"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(purchase_orders.router, prefix="/procurement", tags=["procurement"])
