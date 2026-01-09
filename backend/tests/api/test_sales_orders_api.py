"""
API tests for Sales Orders endpoints.
"""

from decimal import Decimal
from uuid import UUID

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.tests.conftest import create_test_inventory_item


def _create_customer(client: TestClient):
    r = client.post(
        "/api/v1/customers/",
        json={
            "name": "Beta LLC",
            "email": "orders@beta.com",
        },
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 201
    return r.json()["data"]["id"]


def test_sales_order_lifecycle(client: TestClient, db: Session):
    # Prepare inventory item
    item = create_test_inventory_item(db, name="Widget", unit_price=5.5)
    item_id = item["id"]

    # Prepare customer
    customer_id = _create_customer(client)

    # Create sales order
    payload = {
        "customerId": customer_id,
        "priority": "normal",
        "orderDate": "2026-01-08T10:00:00Z",
        "expectedShipDate": "2026-01-10T10:00:00Z",
        "notes": "Handle with care",
        "lineItems": [
            {
                "itemId": item_id,
                "quantityOrdered": 3,
                "unitPrice": "5.50"
            }
        ]
    }
    r = client.post(
        "/api/v1/sales-orders/",
        json=payload,
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 201
    so = r.json()["data"]
    so_id = so["id"]
    assert UUID(so_id)
    assert so["orderNumber"].startswith("SO-")
    assert so["subtotal"] == "16.50"
    assert so["totalAmount"] == "16.50"

    # Get sales order
    r = client.get(
        f"/api/v1/sales-orders/{so_id}",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    detail = r.json()["data"]
    assert detail["customer"]["id"] == customer_id
    assert len(detail["lineItems"]) == 1

    # Update sales order (add shipping cost)
    upd = {"shippingCost": "4.00"}
    r = client.put(
        f"/api/v1/sales-orders/{so_id}",
        json=upd,
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    updated = r.json()["data"]
    assert updated["shippingCost"] == "4.00"
    assert updated["totalAmount"] == "20.50"

    # Status transitions: draft -> confirmed -> picked -> shipped
    r = client.put(
        f"/api/v1/sales-orders/{so_id}/status",
        json={"status": "confirmed"},
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "confirmed"

    r = client.put(
        f"/api/v1/sales-orders/{so_id}/status",
        json={"status": "picked"},
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "picked"

    r = client.put(
        f"/api/v1/sales-orders/{so_id}/status",
        json={"status": "shipped", "notes": "Tracking #123"},
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "shipped"


def test_list_sales_orders_filters(client: TestClient, db: Session):
    # Prepare inventory items
    item_a = create_test_inventory_item(db, name="Gadget", unit_price=10.0)
    item_b = create_test_inventory_item(db, name="Thing", unit_price=2.0)
    cust_id = _create_customer(client)

    # Create two orders
    for qty, price in [(1, "10.00"), (2, "2.00")]:
        r = client.post(
            "/api/v1/sales-orders",
            json={
                "customerId": cust_id,
                "priority": "high",
                "lineItems": [
                    {"itemId": item_a["id"], "quantityOrdered": qty, "unitPrice": price}
                ],
            },
            headers={"X-Tenant-Slug": "test-tenant"},
        )
        assert r.status_code == 201

    # List
    r = client.get(
        "/api/v1/sales-orders/?page=1&page_size=10&priority=high",
        headers={"X-Tenant-Slug": "test-tenant"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["data"]["totalItems"] >= 2
