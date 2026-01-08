"""
Tests for Item Lot functionality.

Tests cover:
- ItemLot model creation and relationships
- LotService CRUD operations
- API endpoints for lot management
- Error cases (duplicate lot numbers, insufficient quantity, etc.)
"""

import pytest
import uuid
from datetime import date, datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import (
    create_test_inventory_item,
    create_test_location,
)
from app.models.item_lot import ItemLot
from app.models.tenant import DEFAULT_TENANT_ID
from app.services.lot import lot_service


# =============================================================================
# LotService Tests
# =============================================================================


class TestLotServiceCreate:
    """Tests for lot_service.create_lot()"""

    def test_create_lot_success(self, db: Session):
        """Test successful lot creation with all fields."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        location = create_test_location(db, name="Warehouse A", code="WH-A")

        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
            serial_number="SN-12345",
            expiration_date=date.today() + timedelta(days=365),
            manufacture_date=date.today(),
            location_id=uuid.UUID(location["id"]),
        )

        assert lot.lot_number == "LOT-2026-001"
        assert lot.serial_number == "SN-12345"
        assert lot.quantity == 100
        assert lot.expiration_date == date.today() + timedelta(days=365)
        assert lot.manufacture_date == date.today()
        assert str(lot.location_id) == location["id"]

    def test_create_lot_minimal_fields(self, db: Session):
        """Test lot creation with only required fields."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=50,
        )

        assert lot.lot_number == "LOT-2026-001"
        assert lot.quantity == 50
        assert lot.serial_number is None
        assert lot.expiration_date is None
        assert lot.manufacture_date is None
        assert lot.location_id is None

    def test_create_lot_duplicate_lot_number(self, db: Session):
        """Test that duplicate lot numbers per tenant are rejected."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        # Create first lot
        lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        # Try to create second lot with same number
        with pytest.raises(ValueError, match="already exists"):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.UUID(item["id"]),
                lot_number="LOT-2026-001",
                quantity=50,
            )

    def test_create_lot_invalid_quantity(self, db: Session):
        """Test that negative quantity is rejected."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        with pytest.raises(ValueError, match="must be greater than 0"):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.UUID(item["id"]),
                lot_number="LOT-2026-001",
                quantity=0,
            )

    def test_create_lot_item_not_found(self, db: Session):
        """Test that creating lot for non-existent item fails."""
        with pytest.raises(ValueError, match="not found"):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.uuid4(),
                lot_number="LOT-2026-001",
                quantity=100,
            )

    def test_create_lot_location_not_found(self, db: Session):
        """Test that invalid location reference is rejected."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        with pytest.raises(ValueError, match="Location not found"):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.UUID(item["id"]),
                lot_number="LOT-2026-001",
                quantity=100,
                location_id=uuid.uuid4(),
            )


class TestLotServiceRead:
    """Tests for lot_service.get_lots() and get_lot_by_id()"""

    def test_get_lot_by_id(self, db: Session):
        """Test retrieving a lot by ID."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        created_lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        retrieved_lot = lot_service.get_lot_by_id(db, created_lot.id)

        assert retrieved_lot is not None
        assert retrieved_lot.id == created_lot.id
        assert retrieved_lot.lot_number == "LOT-2026-001"

    def test_get_lot_by_id_not_found(self, db: Session):
        """Test that retrieving non-existent lot returns None."""
        lot = lot_service.get_lot_by_id(db, uuid.uuid4())
        assert lot is None

    def test_get_lots_by_item(self, db: Session):
        """Test filtering lots by item."""
        item1 = create_test_inventory_item(db, name="Item 1", sku="TST-001")
        item2 = create_test_inventory_item(db, name="Item 2", sku="TST-002")

        lot1 = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item1["id"]),
            lot_number="LOT-001",
            quantity=100,
        )

        lot2 = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item1["id"]),
            lot_number="LOT-002",
            quantity=200,
        )

        lot3 = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item2["id"]),
            lot_number="LOT-003",
            quantity=150,
        )

        item1_lots = lot_service.get_lots(db, item_id=uuid.UUID(item1["id"]))

        assert len(item1_lots) == 2
        assert any(l.lot_number == "LOT-001" for l in item1_lots)
        assert any(l.lot_number == "LOT-002" for l in item1_lots)

    def test_get_lots_exclude_expired(self, db: Session):
        """Test that expired lots are excluded by default."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        # Create non-expired lot
        lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-VALID",
            quantity=100,
            expiration_date=date.today() + timedelta(days=30),
        )

        # Create expired lot
        lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-EXPIRED",
            quantity=100,
            expiration_date=date.today() - timedelta(days=1),
        )

        lots = lot_service.get_lots(
            db, item_id=uuid.UUID(item["id"]), include_expired=False
        )

        assert len(lots) == 1
        assert lots[0].lot_number == "LOT-VALID"


class TestLotServiceUpdate:
    """Tests for lot_service.update_lot()"""

    def test_update_lot_quantity(self, db: Session):
        """Test updating lot quantity."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        updated_lot = lot_service.update_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            lot_id=lot.id,
            quantity=150,
        )

        assert updated_lot.quantity == 150

    def test_update_lot_serial_number(self, db: Session):
        """Test updating lot serial number."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
            serial_number="SN-OLD",
        )

        updated_lot = lot_service.update_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            lot_id=lot.id,
            serial_number="SN-NEW",
        )

        assert updated_lot.serial_number == "SN-NEW"

    def test_update_lot_lot_number_duplicate(self, db: Session):
        """Test that updating to duplicate lot number fails."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        lot1 = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-001",
            quantity=100,
        )

        lot2 = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-002",
            quantity=100,
        )

        with pytest.raises(ValueError, match="already exists"):
            lot_service.update_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                lot_id=lot2.id,
                lot_number="LOT-001",
            )

    def test_update_lot_invalid_quantity(self, db: Session):
        """Test that invalid quantity update is rejected."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        with pytest.raises(ValueError, match="must be greater than 0"):
            lot_service.update_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                lot_id=lot.id,
                quantity=0,
            )


class TestLotServiceDelete:
    """Tests for lot_service.delete_lot()"""

    def test_delete_lot_success(self, db: Session):
        """Test successful lot deletion."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        lot_service.delete_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            lot_id=lot.id,
        )

        # Verify lot is deleted
        retrieved = lot_service.get_lot_by_id(db, lot.id)
        assert retrieved is None

    def test_delete_lot_not_found(self, db: Session):
        """Test that deleting non-existent lot raises error."""
        with pytest.raises(ValueError, match="not found"):
            lot_service.delete_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                lot_id=uuid.uuid4(),
            )


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestLotAPICreate:
    """Tests for POST /api/v1/inventory/items/{item_id}/lots"""

    def test_create_lot_via_api_success(self, client: TestClient, db: Session):
        """Test successful lot creation via API."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        location = create_test_location(db, name="Warehouse A", code="WH-A")

        payload = {
            "lotNumber": "LOT-2026-001",
            "serialNumber": "SN-12345",
            "quantity": 100,
            "expirationDate": "2027-01-08",
            "manufactureDate": "2025-12-08",
            "locationId": location["id"],
        }

        response = client.post(
            f"/api/v1/inventory/items/{item['id']}/lots",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert "data" in data
        assert data["data"]["lotNumber"] == "LOT-2026-001"
        assert data["data"]["quantity"] == 100

    def test_create_lot_minimal_fields(self, client: TestClient, db: Session):
        """Test lot creation with only required fields."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        payload = {
            "lotNumber": "LOT-2026-001",
            "quantity": 50,
        }

        response = client.post(
            f"/api/v1/inventory/items/{item['id']}/lots",
            json=payload,
        )

        assert response.status_code == 201
        data = response.json()["data"]
        assert data["lotNumber"] == "LOT-2026-001"
        assert data["quantity"] == 50

    def test_create_lot_duplicate_fails(self, client: TestClient, db: Session):
        """Test that duplicate lot number is rejected."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        payload = {
            "lotNumber": "LOT-DUP",
            "quantity": 100,
        }

        # Create first lot
        response1 = client.post(
            f"/api/v1/inventory/items/{item['id']}/lots",
            json=payload,
        )
        assert response1.status_code == 201

        # Try to create duplicate
        response2 = client.post(
            f"/api/v1/inventory/items/{item['id']}/lots",
            json=payload,
        )
        assert response2.status_code == 400


class TestLotAPIRead:
    """Tests for GET /api/v1/inventory/items/{item_id}/lots"""

    def test_get_lots_success(self, client: TestClient, db: Session):
        """Test listing lots with pagination."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        # Create multiple lots
        for i in range(3):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.UUID(item["id"]),
                lot_number=f"LOT-{i:03d}",
                quantity=100 + (i * 10),
            )

        response = client.get(f"/api/v1/inventory/items/{item['id']}/lots")

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "meta" in data
        assert len(data["data"]) == 3
        assert data["meta"]["totalItems"] == 3

    def test_get_lots_with_pagination(self, client: TestClient, db: Session):
        """Test pagination of lots."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        # Create 5 lots
        for i in range(5):
            lot_service.create_lot(
                db=db,
                tenant_id=DEFAULT_TENANT_ID,
                user_id=uuid.uuid4(),
                item_id=uuid.UUID(item["id"]),
                lot_number=f"LOT-{i:03d}",
                quantity=100,
            )

        response = client.get(
            f"/api/v1/inventory/items/{item['id']}/lots?pageSize=2&page=1"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["meta"]["totalItems"] == 5
        assert data["meta"]["totalPages"] == 3

    def test_get_lots_exclude_expired(self, client: TestClient, db: Session):
        """Test that expired lots are excluded by default."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")

        # Create valid lot
        lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-VALID",
            quantity=100,
            expiration_date=date.today() + timedelta(days=30),
        )

        # Create expired lot
        lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-EXPIRED",
            quantity=100,
            expiration_date=date.today() - timedelta(days=1),
        )

        response = client.get(f"/api/v1/inventory/items/{item['id']}/lots")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["lotNumber"] == "LOT-VALID"


class TestLotAPIUpdate:
    """Tests for PUT /api/v1/inventory/lots/{lot_id}"""

    def test_update_lot_success(self, client: TestClient, db: Session):
        """Test successful lot update."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        payload = {
            "quantity": 150,
            "serialNumber": "SN-NEW",
        }

        response = client.put(f"/api/v1/inventory/lots/{lot.id}", json=payload)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["quantity"] == 150
        assert data["serialNumber"] == "SN-NEW"

    def test_update_lot_partial(self, client: TestClient, db: Session):
        """Test partial lot update."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        payload = {"quantity": 120}

        response = client.put(f"/api/v1/inventory/lots/{lot.id}", json=payload)

        assert response.status_code == 200
        data = response.json()["data"]
        assert data["quantity"] == 120
        assert data["lotNumber"] == "LOT-2026-001"  # Unchanged


class TestLotAPIDelete:
    """Tests for DELETE /api/v1/inventory/lots/{lot_id}"""

    def test_delete_lot_success(self, client: TestClient, db: Session):
        """Test successful lot deletion."""
        item = create_test_inventory_item(db, name="Test Item", sku="TST-001")
        lot = lot_service.create_lot(
            db=db,
            tenant_id=DEFAULT_TENANT_ID,
            user_id=uuid.uuid4(),
            item_id=uuid.UUID(item["id"]),
            lot_number="LOT-2026-001",
            quantity=100,
        )

        response = client.delete(f"/api/v1/inventory/lots/{lot.id}")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data

        # Verify lot is deleted
        db.refresh(db)
        deleted_lot = lot_service.get_lot_by_id(db, lot.id)
        assert deleted_lot is None

    def test_delete_lot_not_found(self, client: TestClient, db: Session):
        """Test deleting non-existent lot."""
        fake_id = uuid.uuid4()

        response = client.delete(f"/api/v1/inventory/lots/{fake_id}")

        assert response.status_code == 404
