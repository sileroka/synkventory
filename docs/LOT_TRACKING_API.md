# Item Lot/Serial Number Tracking API Documentation

## Overview

The Item Lot API provides endpoints for managing serial numbers, lot numbers, and batch tracking in Synkventory. This is essential for industries that require traceability for recalls, warranty claims, compliance, or expiration date management.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require JWT authentication via HttpOnly cookie (set automatically on login).

## Endpoints

### 1. List Lots for an Inventory Item

**Endpoint:** `GET /inventory/items/{item_id}/lots`

**Description:** Retrieve all lots for a specific inventory item with optional filtering and pagination.

**Parameters:**

| Name             | Type    | Default    | Description                                            |
| ---------------- | ------- | ---------- | ------------------------------------------------------ |
| `item_id`        | UUID    | Required   | ID of the inventory item                               |
| `page`           | Integer | 1          | Page number for pagination                             |
| `pageSize`       | Integer | 25         | Items per page (max: 1000)                             |
| `locationId`     | UUID    | Optional   | Filter by storage location                             |
| `includeExpired` | Boolean | false      | Include expired lots                                   |
| `orderBy`        | String  | created_at | Sort by: `created_at`, `expiration_date`, `lot_number` |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440000/lots?page=1&pageSize=25&includeExpired=false&orderBy=expiration_date"
```

**Example Response:**

```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440000",
      "itemId": "550e8400-e29b-41d4-a716-446655440000",
      "lotNumber": "LOT-2026-001",
      "serialNumber": "SN-12345",
      "quantity": 100,
      "expirationDate": "2027-01-15",
      "manufactureDate": "2025-12-01",
      "locationId": "770e8400-e29b-41d4-a716-446655440000",
      "createdAt": "2026-01-08T10:30:00Z",
      "updatedAt": "2026-01-08T10:30:00Z",
      "createdBy": "880e8400-e29b-41d4-a716-446655440000",
      "item": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "Widget A",
        "sku": "WGT-001"
      },
      "location": {
        "id": "770e8400-e29b-41d4-a716-446655440000",
        "name": "Warehouse A",
        "code": "WH-A"
      }
    }
  ],
  "meta": {
    "page": 1,
    "pageSize": 25,
    "totalItems": 1,
    "totalPages": 1,
    "timestamp": "2026-01-08T10:30:00Z",
    "requestId": "req-12345"
  }
}
```

**Status Codes:**

- `200 OK` - Lots retrieved successfully
- `400 Bad Request` - Invalid query parameters
- `401 Unauthorized` - Missing or invalid authentication

---

### 2. Create a New Lot

**Endpoint:** `POST /inventory/items/{item_id}/lots`

**Description:** Create a new lot/serial number for an inventory item.

**Request Body:**

```json
{
  "lotNumber": "LOT-2026-001",
  "serialNumber": "SN-12345",
  "quantity": 100,
  "expirationDate": "2027-01-15",
  "manufactureDate": "2025-12-01",
  "locationId": "770e8400-e29b-41d4-a716-446655440000"
}
```

**Field Descriptions:**

| Field             | Type            | Required | Rules                     | Description                    |
| ----------------- | --------------- | -------- | ------------------------- | ------------------------------ |
| `lotNumber`       | String          | Yes      | Must be unique per tenant | Lot identifier                 |
| `serialNumber`    | String          | No       | Max 100 characters        | Serial number for single units |
| `quantity`        | Integer         | Yes      | Must be > 0               | Number of items in lot         |
| `expirationDate`  | Date (ISO 8601) | No       | Must be future date       | Expiration date                |
| `manufactureDate` | Date (ISO 8601) | No       | May be past               | Production date                |
| `locationId`      | UUID            | No       | Must be valid location    | Storage location               |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/items/550e8400-e29b-41d4-a716-446655440000/lots" \
  -H "Content-Type: application/json" \
  -d '{
    "lotNumber": "LOT-2026-001",
    "serialNumber": "SN-12345",
    "quantity": 100,
    "expirationDate": "2027-01-15",
    "manufactureDate": "2025-12-01",
    "locationId": "770e8400-e29b-41d4-a716-446655440000"
  }'
```

**Example Response:**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "itemId": "550e8400-e29b-41d4-a716-446655440000",
    "lotNumber": "LOT-2026-001",
    "serialNumber": "SN-12345",
    "quantity": 100,
    "expirationDate": "2027-01-15",
    "manufactureDate": "2025-12-01",
    "locationId": "770e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2026-01-08T10:30:00Z",
    "createdBy": "880e8400-e29b-41d4-a716-446655440000"
  },
  "meta": {
    "timestamp": "2026-01-08T10:30:00Z",
    "requestId": "req-12345"
  }
}
```

**Status Codes:**

- `201 Created` - Lot created successfully
- `400 Bad Request` - Invalid input or duplicate lot number
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Item or location not found

**Error Response Example:**

```json
{
  "error": {
    "code": "DUPLICATE_LOT_NUMBER",
    "message": "Lot number 'LOT-2026-001' already exists for this tenant"
  },
  "meta": {
    "timestamp": "2026-01-08T10:30:00Z",
    "requestId": "req-12345"
  }
}
```

---

### 3. Update a Lot

**Endpoint:** `PUT /inventory/lots/{lot_id}`

**Description:** Update an existing lot. All fields are optional.

**Request Body:**

```json
{
  "lotNumber": "LOT-2026-001-UPDATED",
  "serialNumber": "SN-12346",
  "quantity": 95,
  "expirationDate": "2027-02-15",
  "manufactureDate": "2025-12-15",
  "locationId": "770e8400-e29b-41d4-a716-446655440001"
}
```

**Example Request:**

```bash
curl -X PUT "http://localhost:8000/api/v1/inventory/lots/660e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "quantity": 95,
    "expirationDate": "2027-02-15"
  }'
```

**Example Response:**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440000",
    "itemId": "550e8400-e29b-41d4-a716-446655440000",
    "lotNumber": "LOT-2026-001",
    "serialNumber": "SN-12345",
    "quantity": 95,
    "expirationDate": "2027-02-15",
    "manufactureDate": "2025-12-01",
    "locationId": "770e8400-e29b-41d4-a716-446655440000",
    "createdAt": "2026-01-08T10:30:00Z",
    "updatedAt": "2026-01-08T10:45:00Z",
    "createdBy": "880e8400-e29b-41d4-a716-446655440000",
    "updatedBy": "880e8400-e29b-41d4-a716-446655440000"
  },
  "meta": {
    "timestamp": "2026-01-08T10:45:00Z",
    "requestId": "req-12346"
  }
}
```

**Status Codes:**

- `200 OK` - Lot updated successfully
- `400 Bad Request` - Invalid input
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Lot not found

---

### 4. Delete a Lot

**Endpoint:** `DELETE /inventory/lots/{lot_id}`

**Description:** Delete a lot and remove it from inventory tracking. The parent item's total quantity is recalculated.

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/inventory/lots/660e8400-e29b-41d4-a716-446655440000"
```

**Example Response:**

```json
{
  "message": "Lot deleted successfully",
  "meta": {
    "timestamp": "2026-01-08T10:45:00Z",
    "requestId": "req-12347"
  }
}
```

**Status Codes:**

- `200 OK` - Lot deleted successfully
- `401 Unauthorized` - Missing or invalid authentication
- `404 Not Found` - Lot not found

---

## Inventory Item Total Quantity

When lots exist for an inventory item, the item's `total_quantity` property automatically returns the sum of all lot quantities:

```python
item.total_quantity  # Returns: sum(lot.quantity for lot in item.lots)
                     # Falls back to item.quantity if no lots exist
```

This is calculated dynamically and requires no manual updates.

---

## Stock Movement Integration

Stock movements can be linked to specific lots for complete traceability:

```bash
curl -X POST "http://localhost:8000/api/v1/stock-movements" \
  -H "Content-Type: application/json" \
  -d '{
    "inventoryItemId": "550e8400-e29b-41d4-a716-446655440000",
    "movementType": "ship",
    "quantity": 10,
    "fromLocationId": "770e8400-e29b-41d4-a716-446655440000",
    "lotId": "660e8400-e29b-41d4-a716-446655440000",
    "referenceNumber": "ORDER-12345"
  }'
```

**Behavior by Movement Type:**

| Type       | Lot Behavior                                   |
| ---------- | ---------------------------------------------- |
| `receive`  | Lot quantity increases by movement amount      |
| `ship`     | Lot quantity decreases (fails if insufficient) |
| `transfer` | Lot quantity decreases, location updated       |
| `adjust`   | Lot quantity adjusted (based on sign)          |

---

## Purchase Order Integration

When receiving purchase orders, lots can be created inline:

```bash
curl -X POST "http://localhost:8000/api/v1/purchase-orders/po-uuid/receive" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "lineItemId": "line-item-uuid",
        "quantityReceived": 50,
        "lots": [
          {
            "lotNumber": "LOT-2026-001",
            "serialNumber": null,
            "quantity": 30,
            "expirationDate": "2027-01-15",
            "manufactureDate": "2025-12-01"
          },
          {
            "lotNumber": "LOT-2026-002",
            "serialNumber": null,
            "quantity": 20,
            "expirationDate": "2027-02-28",
            "manufactureDate": "2026-01-01"
          }
        ]
      }
    ]
  }'
```

---

## Error Handling

### Common Error Codes

| Code                    | HTTP Status | Description                             |
| ----------------------- | ----------- | --------------------------------------- |
| `DUPLICATE_LOT_NUMBER`  | 400         | Lot number already exists for tenant    |
| `INVALID_QUANTITY`      | 400         | Quantity must be greater than 0         |
| `ITEM_NOT_FOUND`        | 404         | Inventory item does not exist           |
| `LOT_NOT_FOUND`         | 404         | Lot does not exist                      |
| `LOCATION_NOT_FOUND`    | 404         | Location does not exist                 |
| `INSUFFICIENT_QUANTITY` | 400         | Lot quantity insufficient for operation |

---

## Best Practices

1. **Unique Lot Numbers:** Use a consistent naming scheme (e.g., `LOT-YYYY-NNNNN`)
2. **Always Set Location:** Specify `locationId` when receiving to maintain physical location tracking
3. **Track Expiration:** Set `expirationDate` for perishable items to enable automatic filtering
4. **Use Serial Numbers:** For high-value items, set `serialNumber` for individual unit tracking
5. **Link Movements:** Always link stock movements to lots when available for complete traceability
6. **Monitor Expiration:** Periodically query with `includeExpired=false` to identify expiring inventory

---

## Examples

### Example 1: Receiving Perishable Items

```bash
# Create lot for fresh produce with 30-day shelf life
curl -X POST "http://localhost:8000/api/v1/inventory/items/produce-item-id/lots" \
  -H "Content-Type: application/json" \
  -d '{
    "lotNumber": "FRESH-2026-01-08",
    "quantity": 200,
    "expirationDate": "2026-02-07",
    "manufactureDate": "2026-01-08",
    "locationId": "refrigerator-location-id"
  }'
```

### Example 2: Tracking Electronics with Serial Numbers

```bash
# Create lot for 5 laptops with individual serial numbers
curl -X POST "http://localhost:8000/api/v1/inventory/items/laptop-item-id/lots" \
  -H "Content-Type: application/json" \
  -d '{
    "lotNumber": "DELL-2026-Q1-BATCH-001",
    "serialNumber": "DELL-12345-67890",
    "quantity": 5,
    "locationId": "electronics-warehouse-id"
  }'
```

### Example 3: Receiving Multi-Lot Purchase Order

```bash
# Receive PO with items from different suppliers/batches
curl -X POST "http://localhost:8000/api/v1/purchase-orders/po-2026-001/receive" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "lineItemId": "line-1",
        "quantityReceived": 50,
        "lots": [
          {
            "lotNumber": "SUPPLIER-A-2026-001",
            "quantity": 50,
            "expirationDate": "2027-01-08"
          }
        ]
      },
      {
        "lineItemId": "line-2",
        "quantityReceived": 75,
        "lots": [
          {
            "lotNumber": "SUPPLIER-B-2026-001",
            "quantity": 75,
            "expirationDate": "2027-03-08"
          }
        ]
      }
    ]
  }'
```

---

## Testing

Unit tests for lot functionality are located in `backend/tests/test_item_lots.py`.

Run tests with:

```bash
cd backend
pytest tests/test_item_lots.py -v
```

Test coverage includes:

- Lot creation, update, deletion
- Duplicate lot number validation
- Quantity validation
- Expiration date filtering
- API endpoint validation
- Error case handling
