"""
API v1 Router - Includes all API endpoints.
"""

from fastapi import APIRouter
from app.api.v1 import (
    inventory,
    locations,
    categories,
    category_attributes,
    stock_movements,
    reports,
    health,
    auth,
    users,
    admin,
    audit_logs,
    uploads,
    bom,
    work_orders,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(bom.router, prefix="/inventory", tags=["bill-of-materials"])
api_router.include_router(work_orders.router, tags=["work-orders"])
api_router.include_router(locations.router, prefix="/locations", tags=["locations"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(category_attributes.router, tags=["category-attributes"])
api_router.include_router(
    stock_movements.router, prefix="/stock-movements", tags=["stock-movements"]
)
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["audit-logs"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["uploads"])

# Admin portal routes (admin.synkventory.com)
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
