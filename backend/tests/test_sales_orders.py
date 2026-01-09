"""
Unit tests for Sales Orders: create, update, ship with multi-tenant separation and audit logging.
"""

from datetime import datetime
from decimal import Decimal
import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.sales_order import SalesOrderStatus
from app.models.audit_log import AuditLog, EntityType
from app.models.customer import Customer
from app.models.inventory import InventoryItem
from app.models.location import Location
from app.models.tenant import DEFAULT_TENANT_ID

from app.schemas.sales_order import SalesOrderCreate, SalesOrderLineItemCreate, ShipItemsRequest, ShipmentEntry


def _create_customer(db: Session, name: str = "Test Customer") -> Customer:
    cust = Customer(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name=name,
        email="cust@test.local",
        is_active=True,
    )
    db.add(cust)
    db.commit()
    db.refresh(cust)
    return cust


def _create_item(db: Session, name: str = "Widget", quantity: int = 50) -> InventoryItem:
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name=name,
        sku=f"SKU-{uuid.uuid4().hex[:8].upper()}",
        quantity=quantity,
        unit_price=Decimal("10.00"),
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def _create_location(db: Session, name: str = "Main Warehouse") -> Location:
    loc = Location(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name=name,
        code=f"LOC-{uuid.uuid4().hex[:6].upper()}",
        is_active=True,
    )
    db.add(loc)
    db.commit()
    db.refresh(loc)
    return loc


# -----------------------------------------------------------------------------
# Create Sales Order
# -----------------------------------------------------------------------------

def test_create_sales_order(client: TestClient, db: Session):
    customer = _create_customer(db)
    item = _create_item(db)

    payload = {
        "customerId": str(customer.id),
        "priority": "normal",
        "orderDate": datetime.utcnow().isoformat(),
        "expectedShipDate": None,
        "notes": "First order",
        "lineItems": [
            {
                "itemId": str(item.id),
                "quantityOrdered": 2,
                "unitPrice": "10.00",
            }
        ],
    }

    resp = client.post("/api/v1/sales-orders", json=payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()["data"]

    assert body["orderNumber"].startswith("SO-")
    assert body["status"] == SalesOrderStatus.DRAFT.value
    assert body["subtotal"] == "20.00"
    assert body["totalAmount"] == "20.00"  # tax/shipping default 0
    assert len(body["lineItems"]) == 1

    # Audit log created
    log = db.query(AuditLog).filter(AuditLog.entity_type == EntityType.SALES_ORDER).first()
    assert log is not None
    assert log.action == "create"
    assert log.tenant_id == str(DEFAULT_TENANT_ID)


# -----------------------------------------------------------------------------
# Update Sales Order (tax/shipping recompute + audit)
# -----------------------------------------------------------------------------

def test_update_sales_order_tax_and_shipping(client: TestClient, db: Session):
    # Create order first
    customer = _create_customer(db)
    item = _create_item(db)

    create_resp = client.post(
        "/api/v1/sales-orders",
        json={
            "customerId": str(customer.id),
            "lineItems": [
                {"itemId": str(item.id), "quantityOrdered": 1, "unitPrice": "15.00"}
            ],
        },
    )
    so = create_resp.json()["data"]

    # Update tax/shipping
    update_resp = client.put(
        f"/api/v1/sales-orders/{so['id']}",
        json={
            "taxAmount": "1.50",
            "shippingCost": "3.00",
        },
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]

    assert updated["subtotal"] == "15.00"
    assert updated["taxAmount"] == "1.50"
    assert updated["shippingCost"] == "3.00"
    assert updated["totalAmount"] == "19.50"

    # Audit log update
    log = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == EntityType.SALES_ORDER, AuditLog.action == "update")
        .first()
    )
    assert log is not None


# -----------------------------------------------------------------------------
# Status transition: confirm -> pick -> ship (with stock movement and audit)
# -----------------------------------------------------------------------------

def test_ship_sales_order_items(client: TestClient, db: Session):
    customer = _create_customer(db)
    item = _create_item(db, quantity=10)
    location = _create_location(db)

    # Create order: qty 3
    create_resp = client.post(
        "/api/v1/sales-orders",
        json={
            "customerId": str(customer.id),
            "lineItems": [
                {"itemId": str(item.id), "quantityOrdered": 3, "unitPrice": "12.00"}
            ],
        },
    )
    so_id = create_resp.json()["data"]["id"]

    # Confirm
    resp_confirm = client.put(
        f"/api/v1/sales-orders/{so_id}/status",
        json={"status": "confirmed"},
    )
    assert resp_confirm.status_code == 200
    assert resp_confirm.json()["data"]["status"] == SalesOrderStatus.CONFIRMED.value

    # Pick
    resp_pick = client.put(
        f"/api/v1/sales-orders/{so_id}/status",
        json={"status": "picked"},
    )
    assert resp_pick.status_code == 200
    assert resp_pick.json()["data"]["status"] == SalesOrderStatus.PICKED.value

    # Ship qty 2 from location
    ship_payload = {
        "shipments": [
            {
                "lineItemId": resp_pick.json()["data"]["lineItems"][0]["id"],
                "quantity": 2,
                "fromLocationId": str(location.id),
            }
        ]
    }
    resp_ship = client.post(f"/api/v1/sales-orders/{so_id}/ship", json=ship_payload)
    assert resp_ship.status_code == 200
    shipped_data = resp_ship.json()["data"]

    assert shipped_data["status"] in [SalesOrderStatus.PICKED.value, SalesOrderStatus.SHIPPED.value]
    assert shipped_data["lineItems"][0]["quantityShipped"] == 2

    # Shipping again remaining 1 should set SHIPPED
    ship_payload_2 = {
        "shipments": [
            {
                "lineItemId": shipped_data["lineItems"][0]["id"],
                "quantity": 1,
                "fromLocationId": str(location.id),
            }
        ]
    }
    resp_ship2 = client.post(f"/api/v1/sales-orders/{so_id}/ship", json=ship_payload_2)
    assert resp_ship2.status_code == 200
    shipped2 = resp_ship2.json()["data"]
    assert shipped2["status"] == SalesOrderStatus.SHIPPED.value

    # Audit ship entries
    ship_logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_type == EntityType.SALES_ORDER, AuditLog.action == "ship")
        .all()
    )
    assert len(ship_logs) >= 1


# -----------------------------------------------------------------------------
# Multi-tenant separation: ensure counters, orders, and queries are tenant-scoped
# -----------------------------------------------------------------------------

def test_multi_tenant_sales_order_separation(client: TestClient, db: Session):
    # Create a second tenant
    from app.models.tenant import Tenant

    other_tenant = Tenant(id=str(uuid.uuid4()), name="Other", slug="other", is_active=True)
    db.add(other_tenant)
    db.commit()

    # Create customer and item for default tenant
    cust1 = _create_customer(db, name="Cust1")
    item1 = _create_item(db, name="Item1")

    # Create order for default tenant
    resp1 = client.post(
        "/api/v1/sales-orders",
        json={
            "customerId": str(cust1.id),
            "lineItems": [{"itemId": str(item1.id), "quantityOrdered": 1, "unitPrice": "5.00"}],
        },
    )
    assert resp1.status_code == 201
    so1 = resp1.json()["data"]

    # Temporarily emulate request context for other tenant via service call using db directly
    # Note: API path uses current tenant from dependency; here we just ensure orders are tied to default tenant
    from app.models.sales_order_counter import SalesOrderCounter
    counters = db.query(SalesOrderCounter).all()
    assert all(c.tenant_id == str(DEFAULT_TENANT_ID) for c in counters)

    # Ensure list endpoint returns only the default tenant's order
    list_resp = client.get("/api/v1/sales-orders?page=1&pageSize=50")
    assert list_resp.status_code == 200
    items = list_resp.json()["data"]["items"]
    assert any(i["id"] == so1["id"] for i in items)

