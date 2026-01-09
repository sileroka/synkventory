"""
API tests for GET /api/v1/purchase-orders with supplier filters.
"""

import uuid
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.tenant import DEFAULT_TENANT_ID
from app.models.user import User
from app.models.purchase_order import PurchaseOrder
from app.models.supplier import Supplier


@pytest.fixture(scope="function")
def auth_client(db: Session) -> Generator[TestClient, None, None]:
    """Test client with DB and auth overrides."""

    def override_get_db():
        try:
            yield db
        finally:
            pass

    # Create a dummy authenticated user if not present
    user = db.query(User).first()
    if user is None:
        user = User(email="tester@example.com", name="Tester", is_active=True)
        db.add(user)
        db.commit()
        db.refresh(user)

    def override_get_current_user():
        return user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def create_supplier(db: Session, name: str) -> Supplier:
    supplier = Supplier(tenant_id=DEFAULT_TENANT_ID, name=name, is_active=True)
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def create_po(
    db: Session,
    po_number: str,
    supplier_id=None,
    supplier_name=None,
) -> PurchaseOrder:
    po = PurchaseOrder(
        tenant_id=DEFAULT_TENANT_ID,
        po_number=po_number,
        supplier_id=supplier_id,
        supplier_name=supplier_name,
    )
    db.add(po)
    db.commit()
    db.refresh(po)
    return po


class TestPurchaseOrdersAPI:
    def test_list_filter_by_supplier_id(self, auth_client: TestClient, db: Session):
        acme = create_supplier(db, name="Acme Corp")
        beta = create_supplier(db, name="Beta LLC")

        create_po(db, po_number="PO-1", supplier_id=acme.id)
        create_po(db, po_number="PO-2", supplier_id=beta.id)
        create_po(db, po_number="PO-3", supplier_name="Acme Legacy")

        resp = auth_client.get(
            f"/api/v1/purchase-orders?supplier_id={acme.id}",
            headers={"X-Tenant-Slug": "demo"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert "data" in body and "meta" in body
        po_numbers = {po["poNumber"] for po in body["data"]}
        assert po_numbers == {"PO-1"}
        assert body["meta"]["totalItems"] == 1

    def test_list_filter_by_supplier_name(self, auth_client: TestClient, db: Session):
        acme = create_supplier(db, name="Acme Corp")
        create_po(db, po_number="PO-10", supplier_id=acme.id)
        create_po(db, po_number="PO-11", supplier_name="Acme Legacy")
        create_po(db, po_number="PO-12", supplier_name="Other Vendor")

        resp = auth_client.get(
            "/api/v1/purchase-orders?supplier_name=Acme",
            headers={"X-Tenant-Slug": "demo"},
        )
        assert resp.status_code == 200
        body = resp.json()
        po_numbers = {po["poNumber"] for po in body["data"]}
        assert "PO-10" in po_numbers and "PO-11" in po_numbers
        assert "PO-12" not in po_numbers
        assert body["meta"]["totalItems"] == 2
