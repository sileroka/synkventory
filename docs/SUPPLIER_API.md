# Supplier Management API Documentation

## Overview

The Supplier Management API provides endpoints for managing supplier information and integrating suppliers with purchase orders. All endpoints require tenant authentication via the `X-Tenant-Slug` header and enforce row-level security for multi-tenant isolation.

## Base URL

```
http://localhost:8000/api/v1
```

## Authentication

All endpoints require:
- Valid tenant context via `X-Tenant-Slug` header
- Authentication token (for authenticated routes)

## Endpoints

### List Suppliers

Get a paginated list of suppliers with optional filtering.

**Endpoint:** `GET /suppliers`

**Query Parameters:**

| Parameter   | Type    | Required | Default | Description                                    |
| ----------- | ------- | -------- | ------- | ---------------------------------------------- |
| `page`      | integer | No       | 1       | Page number                                    |
| `page_size` | integer | No       | 25      | Items per page (max 100)                       |
| `search`    | string  | No       | -       | Search by supplier name, email, or contact     |
| `is_active` | boolean | No       | -       | Filter by active status                        |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/suppliers?page=1&page_size=25&is_active=true" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
{
  "data": {
    "items": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "ACME Industrial Supplies",
        "contactName": "Sarah Johnson",
        "email": "sarah@acme-industrial.com",
        "phone": "+1-555-0101",
        "addressLine1": "1234 Industrial Blvd",
        "addressLine2": null,
        "city": "Chicago",
        "state": "IL",
        "postalCode": "60601",
        "country": "USA",
        "isActive": true,
        "createdAt": "2026-01-08T10:00:00Z",
        "updatedAt": "2026-01-08T10:00:00Z"
      }
    ],
    "total": 8,
    "page": 1,
    "pageSize": 25
  },
  "meta": {
    "timestamp": "2026-01-08T15:30:00Z",
    "requestId": "req-123"
  }
}
```

---

### Get Supplier

Get details for a specific supplier by ID.

**Endpoint:** `GET /suppliers/{id}`

**Path Parameters:**

| Parameter | Type | Required | Description          |
| --------- | ---- | -------- | -------------------- |
| `id`      | UUID | Yes      | The supplier ID      |

**Example Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/suppliers/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ACME Industrial Supplies",
    "contactName": "Sarah Johnson",
    "email": "sarah@acme-industrial.com",
    "phone": "+1-555-0101",
    "addressLine1": "1234 Industrial Blvd",
    "addressLine2": null,
    "city": "Chicago",
    "state": "IL",
    "postalCode": "60601",
    "country": "USA",
    "isActive": true,
    "createdAt": "2026-01-08T10:00:00Z",
    "updatedAt": "2026-01-08T10:00:00Z"
  },
  "meta": {
    "timestamp": "2026-01-08T15:30:00Z",
    "requestId": "req-124"
  }
}
```

**Error Responses:**

- `404 Not Found` - Supplier not found or belongs to different tenant

---

### Create Supplier

Create a new supplier.

**Endpoint:** `POST /suppliers`

**Request Body:**

| Field          | Type    | Required | Description                   |
| -------------- | ------- | -------- | ----------------------------- |
| `name`         | string  | Yes      | Supplier company name         |
| `contactName`  | string  | No       | Primary contact person        |
| `email`        | string  | No       | Contact email address         |
| `phone`        | string  | No       | Contact phone number          |
| `addressLine1` | string  | No       | Street address line 1         |
| `addressLine2` | string  | No       | Street address line 2         |
| `city`         | string  | No       | City                          |
| `state`        | string  | No       | State/Province                |
| `postalCode`   | string  | No       | ZIP/Postal code               |
| `country`      | string  | No       | Country                       |

**Example Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/suppliers" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Global Tech Distributors",
    "contactName": "Michael Chen",
    "email": "m.chen@globaltech.com",
    "phone": "+1-555-0102",
    "addressLine1": "567 Tech Park Drive",
    "addressLine2": "Suite 200",
    "city": "San Jose",
    "state": "CA",
    "postalCode": "95110",
    "country": "USA"
  }'
```

**Example Response:**

```json
{
  "data": {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "name": "Global Tech Distributors",
    "contactName": "Michael Chen",
    "email": "m.chen@globaltech.com",
    "phone": "+1-555-0102",
    "addressLine1": "567 Tech Park Drive",
    "addressLine2": "Suite 200",
    "city": "San Jose",
    "state": "CA",
    "postalCode": "95110",
    "country": "USA",
    "isActive": true,
    "createdAt": "2026-01-08T15:35:00Z",
    "updatedAt": "2026-01-08T15:35:00Z"
  },
  "meta": {
    "timestamp": "2026-01-08T15:35:00Z",
    "requestId": "req-125"
  }
}
```

**Error Responses:**

- `422 Unprocessable Entity` - Validation error (e.g., missing required fields)

---

### Update Supplier

Update an existing supplier. Only provided fields will be updated.

**Endpoint:** `PUT /suppliers/{id}`

**Path Parameters:**

| Parameter | Type | Required | Description     |
| --------- | ---- | -------- | --------------- |
| `id`      | UUID | Yes      | The supplier ID |

**Request Body:** (all fields optional)

| Field          | Type    | Description               |
| -------------- | ------- | ------------------------- |
| `name`         | string  | Supplier company name     |
| `contactName`  | string  | Primary contact person    |
| `email`        | string  | Contact email address     |
| `phone`        | string  | Contact phone number      |
| `addressLine1` | string  | Street address line 1     |
| `addressLine2` | string  | Street address line 2     |
| `city`         | string  | City                      |
| `state`        | string  | State/Province            |
| `postalCode`   | string  | ZIP/Postal code           |
| `country`      | string  | Country                   |

**Example Request:**

```bash
curl -X PUT "http://localhost:8000/api/v1/suppliers/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "phone": "+1-555-0199",
    "email": "newcontact@acme-industrial.com"
  }'
```

**Example Response:**

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "ACME Industrial Supplies",
    "contactName": "Sarah Johnson",
    "email": "newcontact@acme-industrial.com",
    "phone": "+1-555-0199",
    "addressLine1": "1234 Industrial Blvd",
    "addressLine2": null,
    "city": "Chicago",
    "state": "IL",
    "postalCode": "60601",
    "country": "USA",
    "isActive": true,
    "createdAt": "2026-01-08T10:00:00Z",
    "updatedAt": "2026-01-08T15:40:00Z"
  },
  "meta": {
    "timestamp": "2026-01-08T15:40:00Z",
    "requestId": "req-126"
  }
}
```

**Error Responses:**

- `404 Not Found` - Supplier not found or belongs to different tenant
- `422 Unprocessable Entity` - Validation error

---

### Delete Supplier

Deactivate a supplier (soft delete). The supplier will be marked as inactive but not removed from the database.

**Endpoint:** `DELETE /suppliers/{id}`

**Path Parameters:**

| Parameter | Type | Required | Description     |
| --------- | ---- | -------- | --------------- |
| `id`      | UUID | Yes      | The supplier ID |

**Example Request:**

```bash
curl -X DELETE "http://localhost:8000/api/v1/suppliers/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Example Response:**

```
204 No Content
```

**Error Responses:**

- `404 Not Found` - Supplier not found or belongs to different tenant

---

## Integration with Purchase Orders

Suppliers can be linked to purchase orders to streamline procurement:

### Creating a Purchase Order with Supplier

When creating a purchase order, include the `supplierId` to link it to a supplier:

```bash
curl -X POST "http://localhost:8000/api/v1/purchase-orders" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "supplierId": "550e8400-e29b-41d4-a716-446655440000",
    "priority": "normal",
    "expectedDate": "2026-02-15",
    "receivingLocationId": "location-uuid",
    "lineItems": [
      {
        "itemId": "item-uuid",
        "quantityOrdered": 100,
        "unitPrice": 9.99
      }
    ],
    "notes": "Regular monthly order"
  }'
```

The purchase order will automatically include supplier information in the response.

### Filtering Purchase Orders by Supplier

Filter purchase orders by supplier ID:

```bash
curl -X GET "http://localhost:8000/api/v1/purchase-orders?supplier_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Search by supplier name (works for both linked suppliers and text-only supplier names):

```bash
curl -X GET "http://localhost:8000/api/v1/purchase-orders?supplier_name=ACME" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Audit Logging

All supplier operations (create, update, delete) are automatically logged to the audit trail with:

- Action type (create/update/delete)
- Entity ID (supplier ID)
- Tenant ID
- User who performed the action
- Timestamp
- Changes made (for updates)

Audit logs can be queried via the audit log API:

```bash
curl -X GET "http://localhost:8000/api/v1/audit-logs?entity_type=supplier&entity_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "X-Tenant-Slug: demo" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Multi-Tenant Security

All supplier endpoints enforce multi-tenant isolation via PostgreSQL Row-Level Security (RLS):

- Suppliers are automatically scoped to the current tenant
- Cross-tenant access is prevented at the database level
- Each request must include a valid `X-Tenant-Slug` header
- Attempting to access a supplier from another tenant returns 404

---

## Error Codes

| Code | Description                                              |
| ---- | -------------------------------------------------------- |
| 200  | Success                                                  |
| 201  | Created                                                  |
| 204  | No Content (successful deletion)                         |
| 400  | Bad Request (invalid parameters)                         |
| 404  | Not Found (supplier doesn't exist or wrong tenant)       |
| 422  | Unprocessable Entity (validation error)                  |
| 500  | Internal Server Error                                    |

---

## Best Practices

1. **Search Optimization**: Use the `search` parameter for finding suppliers by name, email, or contact instead of fetching all suppliers.

2. **Active Filtering**: When listing suppliers for selection (e.g., in a dropdown), filter by `is_active=true` to show only active suppliers.

3. **Supplier Linking**: Link purchase orders to suppliers using `supplierId` rather than storing supplier information as text. This enables:
   - Centralized supplier updates
   - Better reporting and analytics
   - Supplier performance tracking

4. **Soft Deletes**: Suppliers are deactivated (not deleted) to preserve historical purchase order references.

5. **Pagination**: Always use pagination for supplier lists to improve performance, especially with large supplier databases.
