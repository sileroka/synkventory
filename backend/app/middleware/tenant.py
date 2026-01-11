"""
Tenant middleware for subdomain-based multi-tenancy.
"""

import logging
import os
from typing import Callable, Optional

from fastapi import Request, Response

logger = logging.getLogger(__name__)
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.tenant import (
    TenantContext,
    clear_current_tenant,
    extract_subdomain,
    set_current_tenant,
)
from app.db.session import get_db
from app.models.tenant import Tenant, DEFAULT_TENANT_ID


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

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
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
            return await call_next(request)

        # Skip tenant check for admin portal endpoints
        if request.url.path.startswith("/api/v1/admin") or request.url.path.startswith(
            "/v1/admin"
        ):
            return await call_next(request)

        # Extract subdomain
        host = request.headers.get("host", "")
        subdomain: Optional[str] = None

        # In dev mode, allow X-Tenant-Slug header override
        # This also supports pytest's TestClient host ("testserver")
        header_slug = request.headers.get("x-tenant-slug") or request.headers.get("X-Tenant-Slug")
        if self.is_dev:
            # In development/test, allow X-Tenant-Slug header override
            # Do NOT fall back to a default tenant - require explicit tenant
            if header_slug:
                subdomain = header_slug
            else:
                # Try to extract from host even in dev (e.g., demo.localhost:4200)
                subdomain = extract_subdomain(host, self.base_domain)
                # For localhost without subdomain, check header is required
                if not subdomain and ("localhost" in host or "testserver" in host):
                    # No tenant specified - block the request
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Tenant not specified. Use X-Tenant-Slug header in development."},
                    )
        else:
            subdomain = extract_subdomain(host, self.base_domain)

        # No subdomain = root domain access = block
        if not subdomain:
            return JSONResponse(
                status_code=404,
                content={"detail": "Not found"},
            )

        # Look up tenant by slug (both dev and prod) using app's DB dependency override when available
        db_session = self._get_db_session(request)
        try:
            tenant_context = self._get_tenant_by_slug(subdomain, db_session)
        finally:
            try:
                db_session.close()
            except Exception:
                pass

        # If tenant not found or inactive, block request early
        if not tenant_context:
            logger.warning(f"Tenant not found for subdomain: {subdomain}")
            return JSONResponse(status_code=404, content={"detail": "Tenant not found"})

        # Set tenant context
        set_current_tenant(tenant_context)

        try:
            response = await call_next(request)
            return response
        finally:
            # Always clear context after request
            clear_current_tenant()

    def _get_tenant_by_slug(self, slug: str, db: Session) -> Optional[TenantContext]:
        """
        Look up tenant by slug using sync SQLAlchemy.
        Returns None if not found or not active.
        """
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

    def _get_db_session(self, request: Request) -> Session:
        """
        Obtain a DB session. Prefer FastAPI dependency override for get_db if present
        (used in tests with SQLite). Fallback to SessionLocal from app.db.session.
        """
        # Try FastAPI dependency override
        try:
            override = request.app.dependency_overrides.get(get_db)
        except Exception:
            override = None

        if override:
            gen = override()
            db = next(gen)
            # Attach generator to session for proper cleanup on close
            def _close():
                try:
                    next(gen)
                except StopIteration:
                    pass
            setattr(db, "_override_gen_close", _close)
            return db

        # Fallback: instantiate SessionLocal directly
        from app.db.session import SessionLocal
        return SessionLocal()
