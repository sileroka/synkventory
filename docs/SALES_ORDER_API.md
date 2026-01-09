# Sales Order API Documentation

## Overview

Endpoints for managing outbound sales orders with line items and status transitions. All requests require `X-Tenant-Slug` and obey row-level security.

## Base URL

`http://localhost:8000/api/v1`

## Endpoints

### List Sales Orders

`GET /sales-orders`

Query params: `page`, `page_size`, `status`, `priority`, `customer_id`

### Get Sales Order

`GET /sales-orders/{id}`

### Create Sales Order

`POST /sales-orders`

Body fields: `customerId`, `priority`, `orderDate`, `expectedShipDate`, `notes`, `lineItems[] { itemId, quantityOrdered, unitPrice, notes }`

### Update Sales Order

`PUT /sales-orders/{id}`

Optional fields; updates totals when tax/shipping change.

### Update Status

`PUT /sales-orders/{id}/status`

Allowed transitions: `draft -> confirmed -> picked -> shipped`; `cancelled` is terminal.

### Ship Items on Sales Order

`POST /sales-orders/{id}/ship`

Request body:

```
{
  "shipments": [
    {
      "lineItemId": "uuid",
      "quantity": 2,
      "fromLocationId": "uuid",      // optional, source location
      "lotId": "uuid"                // optional, ship a specific lot
    }
  ]
}
```

Notes:
- Increments `quantityShipped` per line item
- When all line items are fully shipped, status transitions to `shipped`
- Creates stock movements of type `sale` and audit log entries (`ship`)

### Returns (RMA) – Overview

Planned endpoint to accept returns and reverse stock movements:
- `POST /sales-orders/{id}/returns` with line items and quantities
- Will create stock movements of type `return` and audit logs
- Lot-aware returns supported

## Example

```bash
curl -X POST "http://localhost:8000/api/v1/sales-orders" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -d '{
    "customerId": "uuid",
    "priority": "normal",
    "lineItems": [
      {"itemId": "item-uuid", "quantityOrdered": 2, "unitPrice": 12.50}
    ]
  }'
```

```bash
# Ship items
curl -X POST "http://localhost:8000/api/v1/sales-orders/{id}/ship" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -d '{
    "shipments": [
      {"lineItemId": "line-uuid", "quantity": 2, "fromLocationId": "loc-uuid"}
    ]
  }'
```
