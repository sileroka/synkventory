"""
Tests for tenant middleware and auth tenant enforcement.

Ensures:
- Invalid tenant slug returns 404 before reaching routes
- Token tenant mismatch returns 401 on protected routes
"""

import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.models.tenant import Tenant, DEFAULT_TENANT_ID
from app.models.user import User
from app.core.security import create_token_pair


def test_invalid_tenant_slug_returns_404(client: TestClient):
    """Requests with unknown tenant slug should be blocked by middleware."""
    resp = client.get(
        "/api/v1/categories",
        headers={"X-Tenant-Slug": "unknown-tenant"},
    )
    assert resp.status_code == 404
    assert resp.json().get("detail") in {"Tenant not found", "Not found"}


def test_token_tenant_mismatch_returns_401(db: Session):
    """Protected routes should return 401 when token tenant_id != request tenant."""

    # Create a second active tenant
    other_tenant = Tenant(
        id=str(uuid.uuid4()),
        name="Other Tenant",
        slug="other-tenant",
        is_active=True,
    )
    db.add(other_tenant)
    db.commit()
    db.refresh(other_tenant)

    # Create a user in the default tenant
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        email="user@test.local",
        name="Test User",
        password_hash="irrelevant-for-token",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Create token pair bound to DEFAULT_TENANT_ID
    tokens = create_token_pair(user_id=str(user.id), tenant_id=str(DEFAULT_TENANT_ID), email=user.email)

    # Build a TestClient without overriding get_current_user, only DB
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as local_client:
            # Set cookies with tokens for default tenant
            local_client.cookies.set("access_token", tokens.access_token)
            local_client.cookies.set("refresh_token", tokens.refresh_token)

            # Request protected route under a DIFFERENT tenant slug
            resp = local_client.get(
                "/api/v1/categories",
                headers={"X-Tenant-Slug": other_tenant.slug},
            )
            assert resp.status_code == 401
    finally:
        app.dependency_overrides.clear()


def test_token_tenant_match_allows_access(db: Session):
    """Protected route should succeed when token tenant_id matches request tenant."""

    # Ensure default tenant exists
    default = db.query(Tenant).filter(Tenant.id == str(DEFAULT_TENANT_ID)).first()
    assert default is not None

    # Create a user in the default tenant
    user = User(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        email="match@test.local",
        name="Match User",
        password_hash="irrelevant",
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    tokens = create_token_pair(user_id=str(user.id), tenant_id=str(DEFAULT_TENANT_ID), email=user.email)

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as local_client:
            local_client.cookies.set("access_token", tokens.access_token)
            local_client.cookies.set("refresh_token", tokens.refresh_token)

            resp = local_client.get(
                "/api/v1/categories",
                headers={"X-Tenant-Slug": default.slug},
            )
            assert resp.status_code == 200
    finally:
        app.dependency_overrides.clear()
