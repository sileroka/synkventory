"""
API v1 Router - Updated to include auth endpoints.

INSTRUCTIONS: Replace your existing app/api/v1/api.py with this file.
"""

from fastapi import APIRouter
from app.api.v1 import (
    inventory,
    locations,
    categories,
    stock_movements,
    reports,
    health,
    auth,  # NEW: Auth router
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])  # NEW: Auth endpoints
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(
    stock_movements.router, prefix="/stock-movements", tags=["stock-movements"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
