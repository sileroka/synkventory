"""
Tests for the Inventory API endpoints.

Tests cover:
- Create inventory item (success and duplicate SKU failure)
- Read inventory item (success and not found)
- Update inventory item
- Delete inventory item
- List inventory items with pagination
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import (
    create_test_inventory_item,
    create_test_category,
    create_test_location,
)
from app.models.tenant import DEFAULT_TENANT_ID


class TestCreateInventoryItem:
    """Tests for POST /api/v1/inventory/"""

    def test_create_item_success(self, client: TestClient, db: Session):
        """Test successful creation of an inventory item."""
        payload = {
            "name": "Widget A",
            "sku": "WGT-001",
            "description": "A high-quality widget",
            "quantity": 100,
            "reorderPoint": 10,
            "unitPrice": 29.99,
            "status": "in_stock",
        }

        response = client.post("/api/v1/inventory/", json=payload)

        assert response.status_code == 201
        data = response.json()

        # Check response structure
        assert "data" in data
        assert "meta" in data

        # Check item data
        item = data["data"]
        assert item["name"] == payload["name"]
        assert item["sku"] == payload["sku"]
        assert item["description"] == payload["description"]
        assert item["quantity"] == payload["quantity"]
        assert item["reorderPoint"] == payload["reorderPoint"]
        assert item["unitPrice"] == payload["unitPrice"]
        assert item["status"] == payload["status"]
        assert "id" in item

        # Verify UUID format
        uuid.UUID(item["id"])

    def test_create_item_minimal_fields(self, client: TestClient, db: Session):
        """Test creation with only required fields."""
        payload = {
            "name": "Minimal Item",
            "sku": "MIN-001",
        }

        response = client.post("/api/v1/inventory/", json=payload)

        assert response.status_code == 201
        item = response.json()["data"]
        assert item["name"] == "Minimal Item"
        assert item["sku"] == "MIN-001"
        # Check defaults
        assert item["quantity"] == 0
        assert item["reorderPoint"] == 0
        assert item["unitPrice"] == 0.0
        assert item["status"] == "in_stock"

    def test_create_item_duplicate_sku_failure(self, client: TestClient, db: Session):
        """Test that creating an item with duplicate SKU fails."""
        # Create first item
        create_test_inventory_item(db, name="First Item", sku="DUP-001")

        # Try to create second item with same SKU
        payload = {
            "name": "Second Item",
            "sku": "DUP-001",
        }

        response = client.post("/api/v1/inventory/", json=payload)

        assert response.status_code == 400
        error = response.json()
        assert "SKU already exists" in error.get("detail", str(error))

    def test_create_item_with_category_and_location(
        self, client: TestClient, db: Session
    ):
        """Test creation with category and location references."""
        category = create_test_category(db, name="Electronics", code="ELEC")
        location = create_test_location(db, name="Warehouse A", code="WH-A")

        payload = {
            "name": "Electronic Widget",
            "sku": "EW-001",
            "categoryId": category["id"],
            "locationId": location["id"],
        }

        response = client.post("/api/v1/inventory/", json=payload)

        assert response.status_code == 201
        item = response.json()["data"]
        assert item["categoryId"] == category["id"]
        assert item["locationId"] == location["id"]


class TestReadInventoryItem:
    """Tests for GET /api/v1/inventory/{item_id}"""

    def test_get_item_success(self, client: TestClient, db: Session):
        """Test successful retrieval of an inventory item."""
        created_item = create_test_inventory_item(
            db,
            name="Readable Item",
            sku="READ-001",
            quantity=50,
            unit_price=19.99,
        )

        response = client.get(f"/api/v1/inventory/{created_item['id']}")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "meta" in data

        item = data["data"]
        assert item["id"] == created_item["id"]
        assert item["name"] == "Readable Item"
        assert item["sku"] == "READ-001"
        assert item["quantity"] == 50
        assert item["unitPrice"] == 19.99

    def test_get_item_not_found(self, client: TestClient, db: Session):
        """Test 404 response for non-existent item."""
        non_existent_id = str(uuid.uuid4())

        response = client.get(f"/api/v1/inventory/{non_existent_id}")

        assert response.status_code == 404
        error = response.json()
        assert "not found" in error.get("detail", "").lower()

    def test_get_item_invalid_uuid(self, client: TestClient, db: Session):
        """Test error response for invalid UUID format."""
        response = client.get("/api/v1/inventory/not-a-uuid")

        assert response.status_code == 422  # Validation error


class TestUpdateInventoryItem:
    """Tests for PUT /api/v1/inventory/{item_id}"""

    def test_update_item_success(self, client: TestClient, db: Session):
        """Test successful update of an inventory item."""
        created_item = create_test_inventory_item(
            db,
            name="Original Name",
            sku="UPD-001",
            quantity=100,
        )

        update_payload = {
            "name": "Updated Name",
            "quantity": 150,
            "unitPrice": 24.99,
        }

        response = client.put(
            f"/api/v1/inventory/{created_item['id']}", json=update_payload
        )

        assert response.status_code == 200
        item = response.json()["data"]

        assert item["name"] == "Updated Name"
        assert item["quantity"] == 150
        assert item["unitPrice"] == 24.99
        # SKU should remain unchanged
        assert item["sku"] == "UPD-001"

    def test_update_item_partial(self, client: TestClient, db: Session):
        """Test partial update (only some fields)."""
        created_item = create_test_inventory_item(
            db,
            name="Partial Update Item",
            sku="PART-001",
            quantity=100,
            unit_price=10.00,
        )

        # Update only quantity
        update_payload = {"quantity": 200}

        response = client.put(
            f"/api/v1/inventory/{created_item['id']}", json=update_payload
        )

        assert response.status_code == 200
        item = response.json()["data"]

        assert item["quantity"] == 200
        # Other fields should remain unchanged
        assert item["name"] == "Partial Update Item"
        assert item["unitPrice"] == 10.00

    def test_update_item_not_found(self, client: TestClient, db: Session):
        """Test 404 response when updating non-existent item."""
        non_existent_id = str(uuid.uuid4())

        response = client.put(
            f"/api/v1/inventory/{non_existent_id}", json={"name": "New Name"}
        )

        assert response.status_code == 404

    def test_update_item_status(self, client: TestClient, db: Session):
        """Test updating item status."""
        created_item = create_test_inventory_item(
            db,
            name="Status Test Item",
            sku="STAT-001",
            status="in_stock",
        )

        response = client.put(
            f"/api/v1/inventory/{created_item['id']}", json={"status": "low_stock"}
        )

        assert response.status_code == 200
        assert response.json()["data"]["status"] == "low_stock"


class TestDeleteInventoryItem:
    """Tests for DELETE /api/v1/inventory/{item_id}"""

    def test_delete_item_success(self, client: TestClient, db: Session):
        """Test successful deletion of an inventory item."""
        created_item = create_test_inventory_item(
            db,
            name="To Delete",
            sku="DEL-001",
        )

        response = client.delete(f"/api/v1/inventory/{created_item['id']}")

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data.get("message", "").lower()

        # Verify item is actually deleted
        get_response = client.get(f"/api/v1/inventory/{created_item['id']}")
        assert get_response.status_code == 404

    def test_delete_item_not_found(self, client: TestClient, db: Session):
        """Test 404 response when deleting non-existent item."""
        non_existent_id = str(uuid.uuid4())

        response = client.delete(f"/api/v1/inventory/{non_existent_id}")

        assert response.status_code == 404


class TestListInventoryItems:
    """Tests for GET /api/v1/inventory/"""

    def test_list_items_empty(self, client: TestClient, db: Session):
        """Test listing items when database is empty."""
        response = client.get("/api/v1/inventory/")

        assert response.status_code == 200
        data = response.json()

        assert data["data"] == []
        assert data["meta"]["totalItems"] == 0
        assert data["meta"]["page"] == 1

    def test_list_items_with_data(self, client: TestClient, db: Session):
        """Test listing items with data in database."""
        # Create multiple items
        for i in range(5):
            create_test_inventory_item(
                db,
                name=f"Item {i+1}",
                sku=f"LIST-{i+1:03d}",
            )

        response = client.get("/api/v1/inventory/")

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) == 5
        assert data["meta"]["totalItems"] == 5
        assert data["meta"]["page"] == 1
        assert data["meta"]["pageSize"] == 25  # Default page size

    def test_list_items_pagination(self, client: TestClient, db: Session):
        """Test pagination of inventory items."""
        # Create 30 items
        for i in range(30):
            create_test_inventory_item(
                db,
                name=f"Paginated Item {i+1}",
                sku=f"PAGE-{i+1:03d}",
            )

        # Get first page with page size of 10
        response = client.get("/api/v1/inventory/?page=1&pageSize=10")

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) == 10
        assert data["meta"]["totalItems"] == 30
        assert data["meta"]["totalPages"] == 3
        assert data["meta"]["page"] == 1
        assert data["meta"]["pageSize"] == 10

        # Get second page
        response = client.get("/api/v1/inventory/?page=2&pageSize=10")
        data = response.json()

        assert len(data["data"]) == 10
        assert data["meta"]["page"] == 2

    def test_list_items_search(self, client: TestClient, db: Session):
        """Test searching inventory items by name or SKU."""
        create_test_inventory_item(db, name="Apple Widget", sku="APL-001")
        create_test_inventory_item(db, name="Orange Gadget", sku="ORG-001")
        create_test_inventory_item(db, name="Banana Tool", sku="BAN-001")

        # Search by name
        response = client.get("/api/v1/inventory/?search=apple")

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) == 1
        assert data["data"][0]["name"] == "Apple Widget"

        # Search by SKU
        response = client.get("/api/v1/inventory/?search=ORG")
        data = response.json()

        assert len(data["data"]) == 1
        assert data["data"][0]["sku"] == "ORG-001"

    def test_list_items_filter_by_status(self, client: TestClient, db: Session):
        """Test filtering inventory items by status."""
        create_test_inventory_item(
            db, name="In Stock Item", sku="IS-001", status="in_stock"
        )
        create_test_inventory_item(
            db, name="Low Stock Item", sku="LS-001", status="low_stock"
        )
        create_test_inventory_item(
            db, name="Out of Stock Item", sku="OOS-001", status="out_of_stock"
        )

        # Filter by single status
        response = client.get("/api/v1/inventory/?statuses=low_stock")

        assert response.status_code == 200
        data = response.json()

        assert len(data["data"]) == 1
        assert data["data"][0]["status"] == "low_stock"

        # Filter by multiple statuses
        response = client.get("/api/v1/inventory/?statuses=in_stock&statuses=low_stock")
        data = response.json()

        assert len(data["data"]) == 2

    def test_list_items_sorting(self, client: TestClient, db: Session):
        """Test sorting inventory items."""
        create_test_inventory_item(db, name="Zebra", sku="Z-001", quantity=10)
        create_test_inventory_item(db, name="Apple", sku="A-001", quantity=50)
        create_test_inventory_item(db, name="Mango", sku="M-001", quantity=30)

        # Sort by name ascending (default)
        response = client.get("/api/v1/inventory/?sortField=name&sortOrder=1")

        assert response.status_code == 200
        data = response.json()

        names = [item["name"] for item in data["data"]]
        assert names == ["Apple", "Mango", "Zebra"]

        # Sort by name descending
        response = client.get("/api/v1/inventory/?sortField=name&sortOrder=-1")
        data = response.json()

        names = [item["name"] for item in data["data"]]
        assert names == ["Zebra", "Mango", "Apple"]

        # Sort by quantity
        response = client.get("/api/v1/inventory/?sortField=quantity&sortOrder=1")
        data = response.json()

        quantities = [item["quantity"] for item in data["data"]]
        assert quantities == [10, 30, 50]


class TestBulkOperations:
    """Tests for bulk operations on inventory items."""

    def test_bulk_delete_success(self, client: TestClient, db: Session):
        """Test successful bulk deletion."""
        items = [
            create_test_inventory_item(db, name=f"Bulk Delete {i}", sku=f"BD-{i:03d}")
            for i in range(3)
        ]

        ids_to_delete = [item["id"] for item in items]

        response = client.post(
            "/api/v1/inventory/bulk-delete", json={"ids": ids_to_delete}
        )

        assert response.status_code == 200
        result = response.json()["data"]
        assert result["successCount"] == 3
        assert result["failedIds"] == []

    def test_bulk_delete_partial_failure(self, client: TestClient, db: Session):
        """Test bulk deletion with some non-existent items."""
        item = create_test_inventory_item(db, name="Existing Item", sku="EX-001")
        non_existent_id = str(uuid.uuid4())

        response = client.post(
            "/api/v1/inventory/bulk-delete", json={"ids": [item["id"], non_existent_id]}
        )

        assert response.status_code == 200
        result = response.json()["data"]
        assert result["successCount"] == 1
        assert non_existent_id in result["failedIds"]
