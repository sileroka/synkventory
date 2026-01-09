"""
Pytest configuration and fixtures for Synkventory tests.

Uses SQLite in-memory database for fast test execution.
"""

import os
import sys
import uuid
from typing import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy import String, Text
from sqlalchemy.types import JSON
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.dialects.postgresql import JSONB as PG_JSONB
from sqlalchemy.sql.schema import ColumnDefault
import uuid

# Add backend to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.session import Base, get_db
from app.models.tenant import Tenant, DEFAULT_TENANT_ID
from app.models.user import User, SYSTEM_USER_ID


# =============================================================================
# Test Database Configuration
# =============================================================================

# Use SQLite in-memory for fast tests
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with SQLite-specific settings
test_engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


# Enable foreign key support for SQLite
@event.listens_for(test_engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """
    Create a fresh database for each test function.

    This fixture:
    1. Creates all tables
    2. Seeds required data (default tenant, system user)
    3. Yields the session
    4. Drops all tables after the test
    """
    # Adjust PostgreSQL-specific types for SQLite
    _adjust_types_for_sqlite(Base)

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    session = TestSessionLocal()

    try:
        # Seed required data
        _seed_test_data(session)
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """
    Create a test client with database dependency override.

    Uses the db fixture to ensure fresh database for each test.
    """

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    # Override auth to use seeded system user
    from app.core.deps import get_current_user

    def override_get_current_user():
        return db.query(User).filter(User.id == str(SYSTEM_USER_ID)).first()

    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def default_tenant(db: Session) -> Tenant:
    """Get the default tenant."""
    return db.query(Tenant).filter(Tenant.id == DEFAULT_TENANT_ID).first()


@pytest.fixture
def system_user(db: Session) -> User:
    """Get the system user."""
    return db.query(User).filter(User.id == SYSTEM_USER_ID).first()


# =============================================================================
# Helper Functions
# =============================================================================


def _seed_test_data(db: Session) -> None:
    """Seed required data for tests."""
    # Create default tenant
    default_tenant = Tenant(
        id=str(DEFAULT_TENANT_ID),
        name="Test Tenant",
        slug="test-tenant",
        is_active=True,
    )
    db.add(default_tenant)

    # Create system user
    system_user = User(
        id=str(SYSTEM_USER_ID),
        tenant_id=str(DEFAULT_TENANT_ID),
        email="system@test.local",
        name="System User",
        password_hash="test",
        is_active=True,
    )
    db.add(system_user)

    db.commit()


def _adjust_types_for_sqlite(base) -> None:
    """Adjust PostgreSQL-specific column types and defaults for SQLite tests."""
    metadata = base.metadata
    for table in metadata.tables.values():
        for col in table.columns:
            # Map PostgreSQL UUID to SQLite-friendly String(36)
            if isinstance(col.type, PG_UUID):
                col.type = String(36)
                # Remove PostgreSQL-specific server_default gen_random_uuid()
                if col.server_default is not None:
                    try:
                        sd = str(col.server_default.arg)
                    except Exception:
                        sd = str(col.server_default)
                    if "gen_random_uuid" in sd:
                        col.server_default = None
                # Ensure Python-side default generates string UUID
                if col.default is not None:
                    try:
                        arg = col.default.arg
                    except Exception:
                        arg = None
                    if arg == uuid.uuid4:
                        col.default = ColumnDefault(lambda: str(uuid.uuid4()))

            # Map PostgreSQL JSONB to generic JSON type for SQLite
            if isinstance(col.type, PG_JSONB):
                col.type = JSON()


# =============================================================================
# Test Data Factories
# =============================================================================


def create_test_inventory_item(
    db: Session,
    name: str = "Test Item",
    sku: str = None,
    quantity: int = 100,
    reorder_point: int = 10,
    unit_price: float = 9.99,
    status: str = "in_stock",
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID,
    **kwargs,
) -> dict:
    """
    Create a test inventory item in the database.

    Returns the item as a dictionary for API comparison.
    """
    from app.models.inventory import InventoryItem

    if sku is None:
        sku = f"TEST-{uuid.uuid4().hex[:8].upper()}"

    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(tenant_id),
        name=name,
        sku=sku,
        quantity=quantity,
        reorder_point=reorder_point,
        unit_price=unit_price,
        status=status,
        **({"custom_attributes": "{}"} | kwargs),
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        "id": str(item.id),
        "name": item.name,
        "sku": item.sku,
        "quantity": item.quantity,
        "reorderPoint": item.reorder_point,
        "unitPrice": item.unit_price,
        "status": item.status,
    }


def create_test_location(
    db: Session,
    name: str = "Test Location",
    code: str = None,
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID,
    **kwargs,
) -> dict:
    """Create a test location in the database."""
    from app.models.location import Location

    if code is None:
        code = f"LOC-{uuid.uuid4().hex[:6].upper()}"

    location = Location(
        tenant_id=tenant_id, name=name, code=code, is_active=True, **kwargs
    )
    db.add(location)
    db.commit()
    db.refresh(location)

    return {
        "id": str(location.id),
        "name": location.name,
        "code": location.code,
    }


def create_test_category(
    db: Session,
    name: str = "Test Category",
    code: str = None,
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID,
    **kwargs,
) -> dict:
    """Create a test category in the database."""
    from app.models.category import Category

    if code is None:
        code = f"CAT-{uuid.uuid4().hex[:6].upper()}"

    category = Category(
        tenant_id=tenant_id, name=name, code=code, is_active=True, **kwargs
    )
    db.add(category)
    db.commit()
    db.refresh(category)

    return {
        "id": str(category.id),
        "name": category.name,
        "code": category.code,
    }
