"""
Test QR JSON convention for lookup-by-barcode endpoint.
"""

import uuid
import json
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.inventory import InventoryItem
from app.models.tenant import DEFAULT_TENANT_ID


def _create_item(db: Session, name: str = "QR Test Item") -> InventoryItem:
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name=name,
        sku=f"QR-{uuid.uuid4().hex[:8].upper()}",
        quantity=5,
        unit_price=2.5,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_qr_json_lookup(client: TestClient, db: Session):
    item = _create_item(db)
    payload = {"type": "item", "id": str(item.id)}
    value = json.dumps(payload)
    resp = client.get(f"/api/v1/inventory/by-barcode/{value}")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]
    assert data["id"] == str(item.id)
    assert data["sku"].startswith("QR-")
