"""
API tests for Customer endpoints.
"""

from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_list_customers_empty(client: TestClient, db: Session):
    response = client.get(
        "/api/v1/customers/",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["data"]["items"] == []
    assert body["data"]["total"] == 0


def test_create_get_update_delete_customer(client: TestClient, db: Session):
    # Create
    payload = {
        "name": "Acme Corp",
        "email": "sales@acme.com",
        "phone": "+1-555-0100",
        "shippingAddress": {
            "line1": "100 Main St",
            "city": "Austin",
            "state": "TX",
            "postalCode": "78701",
            "country": "USA",
        },
        "billingAddress": {
            "line1": "100 Main St",
            "city": "Austin",
            "state": "TX",
            "postalCode": "78701",
            "country": "USA",
        },
        "notes": "VIP customer",
    }
    r = client.post(
        "/api/v1/customers/",
        json=payload,
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 201
    created = r.json()["data"]
    customer_id = created["id"]
    assert UUID(customer_id)
    assert created["name"] == "Acme Corp"
    assert created["isActive"] is True

    # Get
    r = client.get(
        f"/api/v1/customers/{customer_id}",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    got = r.json()["data"]
    assert got["email"] == "sales@acme.com"

    # Update
    upd = {"phone": "+1-555-0199", "notes": "Preferred shipping: FedEx"}
    r = client.put(
        f"/api/v1/customers/{customer_id}",
        json=upd,
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    updated = r.json()["data"]
    assert updated["phone"] == "+1-555-0199"
    assert "Preferred shipping" in updated["notes"]

    # Delete (soft-deactivate)
    r = client.delete(
        f"/api/v1/customers/{customer_id}",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    assert "deactivated" in r.json()["message"].lower()

    # Verify isActive false
    r = client.get(
        f"/api/v1/customers/{customer_id}",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    got = r.json()["data"]
    assert got["isActive"] is False
