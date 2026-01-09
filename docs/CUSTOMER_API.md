# Customer Management API Documentation

## Overview

Endpoints for managing customers and linking them to sales orders. All requests must include `X-Tenant-Slug` and are subject to row-level security.

## Base URL

`http://localhost:8000/api/v1`

## Endpoints

### List Customers

`GET /customers`

Query params: `page`, `page_size`, `search`

### Get Customer

`GET /customers/{id}`

### Create Customer

`POST /customers`

Body fields: `name` (required), `email`, `phone`, `shippingAddress`, `billingAddress`, `notes`

### Update Customer

`PUT /customers/{id}` or `PATCH /customers/{id}`

All fields optional; supports partial updates.

### Deactivate Customer

`DELETE /customers/{id}`

Soft-deactivates customer (historical references preserved).

## Example

```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: demo" \
  -d '{
    "name": "Beta LLC",
    "email": "orders@beta.com",
    "shippingAddress": {"line1": "100 Main St", "city": "Austin"}
  }'
```
