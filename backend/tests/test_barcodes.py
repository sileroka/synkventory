"""
Unit tests for barcode generation endpoint: verifies image storage and metadata persistence.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.inventory import InventoryItem
from app.models.tenant import DEFAULT_TENANT_ID


def _create_item(db: Session, name: str = "Barcode Item") -> InventoryItem:
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name=name,
        sku=f"BC-{uuid.uuid4().hex[:8].upper()}",
        quantity=10,
        unit_price=1.23,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_generate_item_barcode(client: TestClient, db: Session):
    item = _create_item(db)

    resp = client.post(f"/api/v1/inventory/{item.id}/barcode")
    assert resp.status_code == 200, resp.text
    data = resp.json()["data"]

    assert data["barcode"] == item.sku  # default behavior uses SKU if barcode not set
    assert "barcodeImageKey" in data
    assert data["barcodeImageKey"].startswith("barcodes/items/")

    # Ensure DB has persisted values
    refreshed = db.query(InventoryItem).filter(InventoryItem.id == str(item.id)).first()
    assert refreshed.barcode == item.sku
    assert refreshed.barcode_image_key == data["barcodeImageKey"]
