"""
FastAPI application setup with tenant middleware.

INSTRUCTIONS: Replace your existing app/main.py with this file.
"""

import os
import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1.api import api_router
from app.middleware.tenant import TenantMiddleware  # NEW

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add a unique request ID to each request."""
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    return response


# ==========================================================================
# CORS - Updated for subdomain wildcards
# ==========================================================================
# For production, you may want to use allow_origin_regex for subdomains
cors_origins = settings.cors_origins_list

# Add wildcard for subdomains in production
if os.getenv("ENVIRONMENT") == "production":
    cors_origins = []  # Will use regex instead

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=(
        r"https://.*\.synkventory\.com"
        if os.getenv("ENVIRONMENT") == "production"
        else None
    ),
    allow_credentials=True,  # Required for cookies
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================================================
# TENANT MIDDLEWARE - NEW
# Must be added AFTER CORS middleware
# ==========================================================================
app.add_middleware(
    TenantMiddleware,
    base_domain=os.getenv("BASE_DOMAIN", "synkventory.com"),
)

# Register exception handlers
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API router
# Mount at both /api/v1 (direct access) and /v1 (when proxy strips /api)
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router, prefix="/v1")


@app.on_event("startup")
async def startup_event():
    """Application startup event."""
    from app.models.tenant import Tenant
    from app.models.user import User
    from app.models.inventory import InventoryItem
    from app.models.location import Location
    from app.models.category import Category
    from app.models.stock_movement import StockMovement
    from app.models.inventory_location_quantity import InventoryLocationQuantity

    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}")


@app.get("/")
def root():
    return {
        "message": "Welcome to Synkventory API",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
    }
