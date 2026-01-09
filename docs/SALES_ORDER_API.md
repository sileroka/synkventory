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
