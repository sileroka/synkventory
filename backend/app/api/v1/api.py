from fastapi import APIRouter
from app.api.v1 import inventory, locations, categories, stock_movements

api_router = APIRouter()
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(
    stock_movements.router, prefix="/stock-movements", tags=["stock-movements"]
)
