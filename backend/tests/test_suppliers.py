"""
Tests for Supplier API endpoints.

Tests cover:
- Creating, reading, updating suppliers
- Multi-tenant isolation
- Audit logging
- Validation and error handling
"""

import uuid
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.tenant import DEFAULT_TENANT_ID
from app.models.supplier import Supplier
from app.models.audit_log import AuditLog


# =============================================================================
# Test Data Helpers
# =============================================================================


def create_test_supplier(
    db: Session,
    name: str = "Test Supplier",
    contact_name: str = "John Doe",
    email: str = "john@supplier.com",
    phone: str = "+1-555-0100",
    tenant_id: uuid.UUID = DEFAULT_TENANT_ID,
    **kwargs
) -> Supplier:
    """Create a test supplier in the database."""
    supplier = Supplier(
        tenant_id=tenant_id,
        name=name,
        contact_name=contact_name,
        email=email,
        phone=phone,
        **kwargs
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


# =============================================================================
# List Suppliers Tests
# =============================================================================


def test_list_suppliers_empty(client: TestClient, db: Session):
    """Test listing suppliers when none exist."""
    response = client.get(
        "/api/v1/suppliers",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["items"] == []
    assert data["data"]["total"] == 0


def test_list_suppliers(client: TestClient, db: Session):
    """Test listing suppliers successfully."""
    # Create test suppliers
    create_test_supplier(db, name="Supplier A", email="a@supplier.com")
    create_test_supplier(db, name="Supplier B", email="b@supplier.com")
    create_test_supplier(db, name="Supplier C", email="c@supplier.com", is_active=False)
    
    response = client.get(
        "/api/v1/suppliers",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 3
    assert data["data"]["total"] == 3
    
    # Verify supplier structure
    supplier = data["data"]["items"][0]
    assert "id" in supplier
    assert "name" in supplier
    assert "contactName" in supplier
    assert "email" in supplier
    assert "phone" in supplier
    assert "isActive" in supplier


def test_list_suppliers_pagination(client: TestClient, db: Session):
    """Test supplier list pagination."""
    # Create 15 suppliers
    for i in range(15):
        create_test_supplier(db, name=f"Supplier {i}", email=f"supplier{i}@test.com")
    
    # Get first page
    response = client.get(
        "/api/v1/suppliers?page=1&page_size=10",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 10
    assert data["data"]["total"] == 15
    assert data["data"]["page"] == 1
    assert data["data"]["pageSize"] == 10
    
    # Get second page
    response = client.get(
        "/api/v1/suppliers?page=2&page_size=10",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 5
    assert data["data"]["total"] == 15


def test_list_suppliers_search(client: TestClient, db: Session):
    """Test supplier search functionality."""
    create_test_supplier(db, name="ACME Corporation", email="info@acme.com")
    create_test_supplier(db, name="Tech Supplies Inc", email="sales@techsup.com")
    create_test_supplier(db, name="Office Depot", email="orders@depot.com")
    
    # Search by name
    response = client.get(
        "/api/v1/suppliers?search=ACME",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["name"] == "ACME Corporation"
    
    # Search by email
    response = client.get(
        "/api/v1/suppliers?search=depot",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["name"] == "Office Depot"


def test_list_suppliers_active_filter(client: TestClient, db: Session):
    """Test filtering suppliers by active status."""
    create_test_supplier(db, name="Active Supplier", is_active=True)
    create_test_supplier(db, name="Inactive Supplier", is_active=False)
    
    # Get only active
    response = client.get(
        "/api/v1/suppliers?is_active=true",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["name"] == "Active Supplier"


# =============================================================================
# Get Supplier Tests
# =============================================================================


def test_get_supplier_success(client: TestClient, db: Session):
    """Test getting a single supplier by ID."""
    supplier = create_test_supplier(
        db,
        name="Test Supplier",
        contact_name="Jane Smith",
        email="jane@supplier.com",
        phone="+1-555-0200",
        address_line1="123 Main St",
        city="Springfield",
        state="IL",
        postal_code="62701",
        country="USA"
    )
    
    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(supplier.id)
    assert data["name"] == "Test Supplier"
    assert data["contactName"] == "Jane Smith"
    assert data["email"] == "jane@supplier.com"
    assert data["phone"] == "+1-555-0200"
    assert data["addressLine1"] == "123 Main St"
    assert data["city"] == "Springfield"
    assert data["state"] == "IL"
    assert data["postalCode"] == "62701"
    assert data["country"] == "USA"


def test_get_supplier_not_found(client: TestClient, db: Session):
    """Test getting a non-existent supplier."""
    fake_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/suppliers/{fake_id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 404


# =============================================================================
# Create Supplier Tests
# =============================================================================


def test_create_supplier_success(client: TestClient, db: Session):
    """Test creating a supplier successfully."""
    supplier_data = {
        "name": "New Supplier",
        "contactName": "Bob Johnson",
        "email": "bob@newsupplier.com",
        "phone": "+1-555-0300",
        "addressLine1": "456 Oak Ave",
        "city": "Chicago",
        "state": "IL",
        "postalCode": "60601",
        "country": "USA"
    }
    
    response = client.post(
        "/api/v1/suppliers",
        json=supplier_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "New Supplier"
    assert data["contactName"] == "Bob Johnson"
    assert data["email"] == "bob@newsupplier.com"
    assert data["isActive"] is True
    assert "id" in data
    assert "createdAt" in data
    
    # Verify in database
    supplier = db.query(Supplier).filter(Supplier.id == uuid.UUID(data["id"])).first()
    assert supplier is not None
    assert supplier.name == "New Supplier"
    assert supplier.tenant_id == DEFAULT_TENANT_ID


def test_create_supplier_minimal_data(client: TestClient, db: Session):
    """Test creating a supplier with minimal required data."""
    supplier_data = {
        "name": "Minimal Supplier"
    }
    
    response = client.post(
        "/api/v1/suppliers",
        json=supplier_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "Minimal Supplier"
    assert data["contactName"] is None
    assert data["email"] is None


def test_create_supplier_duplicate_name_allowed(client: TestClient, db: Session):
    """Test that duplicate supplier names are allowed (same company, different contacts)."""
    create_test_supplier(db, name="ACME Corp")
    
    supplier_data = {
        "name": "ACME Corp",
        "contactName": "Different Contact",
        "email": "different@acme.com"
    }
    
    response = client.post(
        "/api/v1/suppliers",
        json=supplier_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 201


def test_create_supplier_validates_name(client: TestClient, db: Session):
    """Test that supplier name is required."""
    supplier_data = {
        "contactName": "John Doe"
    }
    
    response = client.post(
        "/api/v1/suppliers",
        json=supplier_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 422


def test_create_supplier_creates_audit_log(client: TestClient, db: Session):
    """Test that creating a supplier creates an audit log entry."""
    supplier_data = {
        "name": "Audited Supplier",
        "email": "audit@supplier.com"
    }
    
    response = client.post(
        "/api/v1/suppliers",
        json=supplier_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 201
    supplier_id = uuid.UUID(response.json()["data"]["id"])
    
    # Check audit log
    audit = db.query(AuditLog).filter(
        AuditLog.entity_type == "supplier",
        AuditLog.entity_id == supplier_id,
        AuditLog.action == "create"
    ).first()
    
    assert audit is not None
    assert audit.tenant_id == DEFAULT_TENANT_ID


# =============================================================================
# Update Supplier Tests
# =============================================================================


def test_update_supplier_success(client: TestClient, db: Session):
    """Test updating a supplier successfully."""
    supplier = create_test_supplier(db, name="Old Name", email="old@email.com")
    
    update_data = {
        "name": "Updated Name",
        "email": "new@email.com",
        "phone": "+1-555-9999"
    }
    
    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        json=update_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Updated Name"
    assert data["email"] == "new@email.com"
    assert data["phone"] == "+1-555-9999"
    
    # Verify in database
    db.refresh(supplier)
    assert supplier.name == "Updated Name"
    assert supplier.email == "new@email.com"


def test_update_supplier_partial(client: TestClient, db: Session):
    """Test partial update of supplier."""
    supplier = create_test_supplier(
        db,
        name="Original",
        email="original@test.com",
        phone="+1-555-0000"
    )
    
    update_data = {
        "phone": "+1-555-1111"
    }
    
    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        json=update_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["name"] == "Original"  # Unchanged
    assert data["email"] == "original@test.com"  # Unchanged
    assert data["phone"] == "+1-555-1111"  # Updated


def test_update_supplier_not_found(client: TestClient, db: Session):
    """Test updating a non-existent supplier."""
    fake_id = uuid.uuid4()
    update_data = {"name": "Updated"}
    
    response = client.put(
        f"/api/v1/suppliers/{fake_id}",
        json=update_data,
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 404


def test_update_supplier_creates_audit_log(client: TestClient, db: Session):
    """Test that updating a supplier creates an audit log entry."""
    supplier = create_test_supplier(db, name="Original")
    
    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        json={"name": "Updated"},
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    
    # Check audit log
    audit = db.query(AuditLog).filter(
        AuditLog.entity_type == "supplier",
        AuditLog.entity_id == supplier.id,
        AuditLog.action == "update"
    ).first()
    
    assert audit is not None


# =============================================================================
# Delete Supplier Tests
# =============================================================================


def test_delete_supplier_success(client: TestClient, db: Session):
    """Test deleting (deactivating) a supplier."""
    supplier = create_test_supplier(db, name="To Delete")
    
    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 204
    
    # Verify supplier is deactivated, not deleted
    db.refresh(supplier)
    assert supplier.is_active is False


def test_delete_supplier_not_found(client: TestClient, db: Session):
    """Test deleting a non-existent supplier."""
    fake_id = uuid.uuid4()
    
    response = client.delete(
        f"/api/v1/suppliers/{fake_id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 404


def test_delete_supplier_creates_audit_log(client: TestClient, db: Session):
    """Test that deleting a supplier creates an audit log entry."""
    supplier = create_test_supplier(db, name="To Delete")
    
    response = client.delete(
        f"/api/v1/suppliers/{supplier.id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 204
    
    # Check audit log
    audit = db.query(AuditLog).filter(
        AuditLog.entity_type == "supplier",
        AuditLog.entity_id == supplier.id,
        AuditLog.action == "delete"
    ).first()
    
    assert audit is not None


# =============================================================================
# Multi-Tenant Isolation Tests
# =============================================================================


def test_suppliers_isolated_by_tenant(client: TestClient, db: Session):
    """Test that suppliers are properly isolated by tenant."""
    from app.models.tenant import Tenant
    
    # Create another tenant
    other_tenant = Tenant(
        id=uuid.uuid4(),
        name="Other Tenant",
        slug="other-tenant",
        is_active=True
    )
    db.add(other_tenant)
    db.commit()
    
    # Create suppliers in each tenant
    create_test_supplier(db, name="Default Tenant Supplier", tenant_id=DEFAULT_TENANT_ID)
    create_test_supplier(db, name="Other Tenant Supplier", tenant_id=other_tenant.id)
    
    # List suppliers for default tenant
    response = client.get(
        "/api/v1/suppliers",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["name"] == "Default Tenant Supplier"
    
    # List suppliers for other tenant
    response = client.get(
        "/api/v1/suppliers",
        headers={"X-Tenant-Slug": "other-tenant"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1
    assert data["data"]["items"][0]["name"] == "Other Tenant Supplier"


def test_cannot_access_supplier_from_other_tenant(client: TestClient, db: Session):
    """Test that a supplier from one tenant cannot be accessed by another."""
    from app.models.tenant import Tenant
    
    # Create another tenant
    other_tenant = Tenant(
        id=uuid.uuid4(),
        name="Other Tenant",
        slug="other-tenant",
        is_active=True
    )
    db.add(other_tenant)
    db.commit()
    
    # Create supplier in other tenant
    supplier = create_test_supplier(
        db,
        name="Other Tenant Supplier",
        tenant_id=other_tenant.id
    )
    
    # Try to access from default tenant
    response = client.get(
        f"/api/v1/suppliers/{supplier.id}",
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 404


def test_cannot_update_supplier_from_other_tenant(client: TestClient, db: Session):
    """Test that a supplier from one tenant cannot be updated by another."""
    from app.models.tenant import Tenant
    
    # Create another tenant
    other_tenant = Tenant(
        id=uuid.uuid4(),
        name="Other Tenant",
        slug="other-tenant",
        is_active=True
    )
    db.add(other_tenant)
    db.commit()
    
    # Create supplier in other tenant
    supplier = create_test_supplier(
        db,
        name="Other Tenant Supplier",
        tenant_id=other_tenant.id
    )
    
    # Try to update from default tenant
    response = client.put(
        f"/api/v1/suppliers/{supplier.id}",
        json={"name": "Hacked Name"},
        headers={"X-Tenant-Slug": "test-tenant"}
    )
    
    assert response.status_code == 404
    
    # Verify supplier was not updated
    db.refresh(supplier)
    assert supplier.name == "Other Tenant Supplier"
