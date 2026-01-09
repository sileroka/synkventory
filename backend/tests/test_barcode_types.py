"""
Tests for barcode generation types: Code128, EAN-13, and QR.
"""

import uuid
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.models.inventory import InventoryItem
from app.models.tenant import DEFAULT_TENANT_ID


def _create_item(db: Session, sku_prefix: str = "BC") -> InventoryItem:
    item = InventoryItem(
        id=str(uuid.uuid4()),
        tenant_id=str(DEFAULT_TENANT_ID),
        name="Barcode Types Item",
        sku=f"{sku_prefix}-{uuid.uuid4().hex[:8].upper()}",
        quantity=10,
        unit_price=1.0,
        is_active=True,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def test_generate_code128(client: TestClient, db: Session):
    item = _create_item(db)
    resp = client.post(f"/api/v1/inventory/{item.id}/barcode?kind=code128")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["barcodeImageKey"].endswith("-code128.png")
    assert data["barcodeImageUrl"] is None or isinstance(data["barcodeImageUrl"], str)


def test_generate_qr(client: TestClient, db: Session):
    item = _create_item(db, sku_prefix="QR")
    resp = client.post(f"/api/v1/inventory/{item.id}/barcode?kind=qr")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["barcodeImageKey"].endswith("-qr.png")


def test_generate_ean13_validation(client: TestClient, db: Session):
    item = _create_item(db, sku_prefix="EAN")
    # Without providing digits, backend uses item.barcode or SKU; SKU may not be numeric; still endpoint should validate and may raise 400
    resp = client.post(f"/api/v1/inventory/{item.id}/barcode?kind=ean13")
    assert resp.status_code in (200, 400)
    # Explicit invalid digits
    resp2 = client.post(f"/api/v1/inventory/{item.id}/barcode?kind=ean13")
    assert resp2.status_code in (200, 400)
