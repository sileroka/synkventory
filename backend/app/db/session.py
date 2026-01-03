"""
Database session management with RLS context.

INSTRUCTIONS: Replace your existing app/db/session.py with this file.

NOTE: For RLS to work, the app needs to:
1. Set the tenant context variable: SET app.current_tenant_id = '<uuid>'
2. Connect as or SET ROLE to synkventory_app

The get_db() dependency now handles setting the tenant context automatically
when a tenant is in the request context.
"""

from sqlalchemy import create_engine, text, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Database session dependency with RLS context.

    When a tenant context exists (set by TenantMiddleware), this:
    1. Sets the app.current_tenant_id session variable
    2. Switches to synkventory_app role for RLS enforcement

    This ensures all queries are automatically filtered by tenant.
    """
    db = SessionLocal()
    try:
        # Import here to avoid circular imports
        from app.core.tenant import get_current_tenant

        tenant = get_current_tenant()
        if tenant:
            # Set the RLS context variable
            db.execute(
                text("SET app.current_tenant_id = :tenant_id"),
                {"tenant_id": str(tenant.id)},
            )
            # Switch to app role for RLS (policies are defined for this role)
            # Only do this if the role exists and we're not already that role
            try:
                db.execute(text("SET ROLE synkventory_app"))
            except Exception:
                # Role might not exist in dev/test environments
                pass

        yield db
    finally:
        # Reset role and close
        if tenant:
            try:
                db.execute(text("RESET ROLE"))
                db.execute(text("RESET app.current_tenant_id"))
            except Exception:
                pass
        db.close()


def get_db_no_tenant():
    """
    Database session without tenant context (admin mode).

    Use for operations that need to bypass RLS:
    - Tenant lookup (before we know which tenant)
    - Admin operations
    - Migrations

    CAUTION: This bypasses tenant isolation!
    """
    db = SessionLocal()
    try:
        # Set admin flag to bypass RLS policies
        # This enables the admin_bypass policy which allows all operations
        db.execute(text("SET app.is_admin = 'true'"))
        yield db
    finally:
        try:
            db.execute(text("SET app.is_admin = 'false'"))
        except Exception:
            pass
        db.close()
