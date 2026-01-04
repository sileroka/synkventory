"""
FastAPI application setup with tenant middleware.

INSTRUCTIONS: Replace your existing app/main.py with this file.
"""

import os
import uuid
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler,
)
from app.api.v1.api import api_router
from app.middleware.tenant import TenantMiddleware  # NEW

# Configure debug logging
logging.basicConfig(level=logging.DEBUG if settings.DEBUG else logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    # Disable automatic trailing slash redirects - they break reverse proxy routing
    # when the proxy strips a path prefix (e.g., /api -> /)
    redirect_slashes=False,
)

# ==========================================================================
# PROXY HEADERS MIDDLEWARE - Trust X-Forwarded-* headers from load balancer
# This ensures redirects use HTTPS when behind a proxy/load balancer
# ==========================================================================
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=["*"])


@app.middleware("http")
async def debug_logging_middleware(request: Request, call_next):
    """Log request details for debugging."""
    # Log incoming request
    logger.info(f"[DEBUG] Incoming request: {request.method} {request.url.path}")
    logger.info(f"[DEBUG] Full URL: {request.url}")
    logger.info(f"[DEBUG] Host header: {request.headers.get('host', 'N/A')}")
    logger.info(f"[DEBUG] X-Forwarded-Proto: {request.headers.get('x-forwarded-proto', 'N/A')}")
    logger.info(f"[DEBUG] X-Forwarded-Host: {request.headers.get('x-forwarded-host', 'N/A')}")
    logger.info(f"[DEBUG] X-Tenant-Slug: {request.headers.get('x-tenant-slug', 'N/A')}")
    logger.info(f"[DEBUG] Origin: {request.headers.get('origin', 'N/A')}")
    logger.info(f"[DEBUG] Cookie present: {'cookie' in request.headers}")
    
    response = await call_next(request)
    
    logger.info(f"[DEBUG] Response status: {response.status_code} for {request.method} {request.url.path}")
    
    return response


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
