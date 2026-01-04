"""
Tenant middleware for subdomain-based multi-tenancy.
"""

import os
import logging
from typing import Callable, Optional

from fastapi import Request, Response
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.tenant import (
    TenantContext,
    clear_current_tenant,
    extract_subdomain,
    set_current_tenant,
)
from app.db.session import SessionLocal
from app.models.tenant import Tenant

logger = logging.getLogger(__name__)


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts subdomain from Host header
    2. Validates tenant exists and is active
    3. Sets tenant context for the request
    4. Blocks requests to root domain (no subdomain)
    """

    def __init__(self, app, base_domain: str = "synkventory.com"):
        super().__init__(app)
        self.base_domain = base_domain
        self.is_dev = os.getenv("ENVIRONMENT", "development") == "development"
        logger.info(f"[TENANT] TenantMiddleware initialized with base_domain={base_domain}, is_dev={self.is_dev}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        logger.info(f"[TENANT] Processing request: {request.url.path}")
        
        # Skip tenant check for health endpoints and docs
        skip_paths = [
            "/health",
            "/api/v1/health",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/",
        ]
        if request.url.path in skip_paths or request.url.path.startswith(
            "/api/v1/health"
        ):
            logger.info(f"[TENANT] Skipping tenant check for path: {request.url.path}")
            return await call_next(request)

        # Skip tenant check for admin portal endpoints
        if request.url.path.startswith("/api/v1/admin") or request.url.path.startswith("/v1/admin"):
            logger.info(f"[TENANT] Skipping tenant check for admin path: {request.url.path}")
            return await call_next(request)

        # Extract subdomain
        host = request.headers.get("host", "")
        subdomain: Optional[str] = None

        logger.info(f"[TENANT] Host header: {host}")

        # In dev mode, allow X-Tenant-Slug header override for localhost testing
        if self.is_dev and ("localhost" in host or "127.0.0.1" in host):
            subdomain = request.headers.get("x-tenant-slug")
            if not subdomain:
                # For local dev without header, use demo tenant
                subdomain = "demo"
            logger.info(f"[TENANT] Dev mode - using subdomain: {subdomain}")
        else:
            subdomain = extract_subdomain(host, self.base_domain)
            logger.info(f"[TENANT] Extracted subdomain: {subdomain} from host: {host}")

        # No subdomain = root domain access = block
        if not subdomain:
            logger.warning(f"[TENANT] No subdomain found, returning 404")
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"},
            )

        # Look up tenant
        tenant_context = self._get_tenant_by_slug(subdomain)
        logger.info(f"[TENANT] Tenant lookup result for '{subdomain}': {tenant_context}")

        # Set context (even if None - auth will fail with generic error)
        if tenant_context:
            set_current_tenant(tenant_context)

        try:
            response = await call_next(request)
            return response
        finally:
            # Always clear context after request
            clear_current_tenant()

    def _get_tenant_by_slug(self, slug: str) -> Optional[TenantContext]:
        """
        Look up tenant by slug using sync SQLAlchemy.
        Returns None if not found or not active.
        """
        db: Session = SessionLocal()
        try:
            tenant = db.query(Tenant).filter(Tenant.slug == slug).first()

            if not tenant:
                return None

            if not tenant.is_active:
                return None

            return TenantContext(
                id=tenant.id,
                slug=tenant.slug,
                name=tenant.name,
                is_active=tenant.is_active,
            )
        finally:
            db.close()
