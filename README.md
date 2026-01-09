# Synkventory

A modern web-based inventory management system built with Python/FastAPI backend, Angular/PrimeNG frontend, and PostgreSQL database.

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: Angular 17 with PrimeNG UI components
- **Database**: PostgreSQL 15
- **Containerization**: Docker & Docker Compose

## Features

- ✅ Complete CRUD operations for inventory items
- ✅ **Serial/Lot/Batch tracking** for perishable and regulated items
- ✅ Expiration date and manufacture date tracking
- ✅ Multi-location inventory management with location hierarchy
- ✅ Stock movement tracking with full audit trail
- ✅ Purchase order management with lot-aware receiving
- ✅ Bill of Materials (BOM) for assembly tracking
- ✅ Work order management for production
- ✅ Row-level security (RLS) for multi-tenant isolation
- ✅ RESTful API with automatic documentation (Swagger/OpenAPI)
- ✅ Modern, responsive UI with PrimeNG components
- ✅ PostgreSQL database for reliable data storage
- ✅ Dockerized deployment for easy setup
- ✅ CORS enabled for frontend-backend communication
- ✅ Comprehensive audit logging for compliance

## Project Structure

```
synkventory/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # API routes
│   │   ├── core/              # Configuration
│   │   ├── db/                # Database setup
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   └── main.py            # Application entry point
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/                   # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # Angular components
│   │   │   ├── models/        # TypeScript models
│   │   │   └── services/      # API services
│   │   └── styles.scss        # Global styles
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml         # Docker orchestration
```

## Quick Start with Docker

### Prerequisites

- Docker
- Docker Compose

### Running the Application

1. Clone the repository:

```bash
git clone https://github.com/sileroka/synkventory.git
cd synkventory
```

2. Start all services:

```bash
docker-compose up -d
```

3. Access the application:

   - **Frontend**: http://localhost
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

4. Stop the services:

```bash
docker-compose down
```

## Local Development Setup

### Backend Setup

1. Navigate to the backend directory:

```bash
cd backend
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

5. Start PostgreSQL (or use Docker):

```bash
docker run -d \
  --name synkventory-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=synkventory \
  -p 5432:5432 \
  postgres:15-alpine
```

6. Run the FastAPI server:

```bash
uvicorn app.main:app --reload
```

The backend will be available at http://localhost:8000

### Frontend Setup

1. Navigate to the frontend directory:

```bash
cd frontend
```

2. Install dependencies:

```bash
npm install
```

3. Start the development server:

```bash
npm start
```

The frontend will be available at http://localhost:4200

## API Endpoints

### Inventory Management

- `GET /api/v1/inventory` - List all inventory items
- `GET /api/v1/inventory/{id}` - Get a specific item
- `POST /api/v1/inventory` - Create a new item
- `PUT /api/v1/inventory/{id}` - Update an item
- `DELETE /api/v1/inventory/{id}` - Delete an item

### Lot/Serial Number Tracking

- `GET /api/v1/inventory/items/{item_id}/lots` - List lots for an item with pagination
- `POST /api/v1/inventory/items/{item_id}/lots` - Create a new lot
- `PUT /api/v1/inventory/lots/{lot_id}` - Update a lot
- `DELETE /api/v1/inventory/lots/{lot_id}` - Delete a lot

### Stock Movements

- `GET /api/v1/stock-movements` - List all stock movements
- `POST /api/v1/stock-movements` - Record a stock movement
- `GET /api/v1/stock-movements/{id}` - Get a specific movement

### Purchase Orders

- `GET /api/v1/purchase-orders` - List purchase orders with optional filters
  - Query params: `page`, `page_size`, `status`, `priority`, `include_received`, `supplier_id`, `supplier_name`
- `POST /api/v1/purchase-orders` - Create a purchase order
- `POST /api/v1/purchase-orders/{po_id}/receive` - Receive items with optional lots
- `GET /api/v1/purchase-orders/stats` - Get purchase order statistics
- `POST /api/v1/purchase-orders/from-low-stock` - Create PO from low stock items

### Supplier Management

- `GET /api/v1/suppliers` - List all suppliers with pagination and search
  - Query params: `page`, `page_size`, `search`, `is_active`
- `GET /api/v1/suppliers/{id}` - Get a specific supplier
- `POST /api/v1/suppliers` - Create a new supplier
- `PUT /api/v1/suppliers/{id}` - Update a supplier
- `DELETE /api/v1/suppliers/{id}` - Deactivate a supplier (soft delete)

### Customer Management

- `GET /api/v1/customers` - List customers with pagination and search
  - Query params: `page`, `page_size`, `search`
- `GET /api/v1/customers/{id}` - Get a specific customer
- `POST /api/v1/customers` - Create a customer
- `PUT /api/v1/customers/{id}` - Update a customer
- `DELETE /api/v1/customers/{id}` - Deactivate a customer (soft delete)

### Sales Orders

- `GET /api/v1/sales-orders` - List sales orders with filters
  - Query params: `page`, `page_size`, `status`, `priority`, `customer_id`
- `POST /api/v1/sales-orders` - Create a sales order with line items
- `GET /api/v1/sales-orders/{id}` - Get a sales order detail
- `PUT /api/v1/sales-orders/{id}` - Update a sales order
- `PUT /api/v1/sales-orders/{id}/status` - Update sales order status (draft→confirmed→picked→shipped)
 - `POST /api/v1/sales-orders/{id}/ship` - Ship items from a sales order (creates stock movements, audit logs)

### Health Check

- `GET /health` - Health check endpoint

## Lot/Serial Number Tracking

Synkventory supports advanced lot and serial number tracking for items that require traceability, such as perishable goods, regulated products, or high-value items.

### Overview

The lot tracking system allows you to:

- Track items by lot number, serial number, or batch identifier
- Record expiration and manufacture dates
- Track lot quantity and location
- Link stock movements to specific lots
- Receive purchase orders with multiple lots
- Maintain complete audit trail for compliance

## Supplier Management

Synkventory includes comprehensive supplier management to streamline procurement and maintain vendor relationships.

### Features

- **Centralized Supplier Database**: Store all supplier contact and address information
- **Purchase Order Integration**: Link purchase orders to suppliers for better tracking
- **Supplier Filtering**: Filter purchase orders by supplier to view all orders from a specific vendor
- **Multi-Tenant Isolation**: Suppliers are isolated by tenant for security
- **Audit Trail**: All supplier changes are logged for compliance

### Supplier Properties

| Property       | Type    | Required | Description                   |
| -------------- | ------- | -------- | ----------------------------- |
| `name`         | String  | Yes      | Supplier company name         |
| `contactName`  | String  | No       | Primary contact person        |
| `email`        | String  | No       | Contact email address         |
| `phone`        | String  | No       | Contact phone number          |
| `addressLine1` | String  | No       | Street address line 1         |
| `addressLine2` | String  | No       | Street address line 2         |
| `city`         | String  | No       | City                          |
| `state`        | String  | No       | State/Province                |
| `postalCode`   | String  | No       | ZIP/Postal code               |
| `country`      | String  | No       | Country                       |
| `isActive`     | Boolean | No       | Active status (default: true) |

### Creating a Supplier

```bash
curl -X POST "http://localhost:8000/api/v1/suppliers" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{
    "name": "ACME Industrial Supplies",
    "contactName": "Sarah Johnson",
    "email": "sarah@acme-industrial.com",
    "phone": "+1-555-0101",
    "addressLine1": "1234 Industrial Blvd",
    "city": "Chicago",
    "state": "IL",
    "postalCode": "60601",
    "country": "USA"
  }'
```

### Listing Suppliers

```bash
# List all active suppliers
curl "http://localhost:8000/api/v1/suppliers?is_active=true" \
  -H "X-Tenant-Slug: your-tenant"

# Search suppliers
curl "http://localhost:8000/api/v1/suppliers?search=ACME&page=1&page_size=25" \
  -H "X-Tenant-Slug: your-tenant"
```

### Creating Purchase Orders with Suppliers

Purchase orders can reference a supplier by ID, allowing you to:

- Auto-fill supplier contact information
- Filter purchase orders by supplier
- Track spending per supplier
- Maintain supplier performance history

```bash
curl -X POST "http://localhost:8000/api/v1/purchase-orders" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{
    "supplierId": "supplier-uuid-here",
    "priority": "normal",
    "expectedDate": "2026-02-01",
    "lineItems": [
      {
        "itemId": "item-uuid",
        "quantityOrdered": 100,
        "unitPrice": 9.99
      }
    ]
  }'
```

### Filtering Purchase Orders by Supplier

```bash
# Get all purchase orders from a specific supplier
curl "http://localhost:8000/api/v1/purchase-orders?supplier_id=supplier-uuid" \
  -H "X-Tenant-Slug: your-tenant"

# Search by supplier name (matches both linked suppliers and text-only supplier names)
curl "http://localhost:8000/api/v1/purchase-orders?supplier_name=ACME" \
  -H "X-Tenant-Slug: your-tenant"
```

## Customer Management

Manage outbound relationships and shipping destinations.

### Creating a Customer

```bash
curl -X POST "http://localhost:8000/api/v1/customers" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{
    "name": "Beta LLC",
    "email": "orders@beta.com",
    "shippingAddress": {"line1": "100 Main St", "city": "Austin", "state": "TX", "postalCode": "78701", "country": "USA"}
  }'
```

### Listing Customers

```bash
curl "http://localhost:8000/api/v1/customers?page=1&page_size=25&search=beta" \
  -H "X-Tenant-Slug: your-tenant"
```

## Sales Orders

Outbound order management with pick/pack/ship workflows.

### Creating a Sales Order

```bash
curl -X POST "http://localhost:8000/api/v1/sales-orders" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{
    "customerId": "customer-uuid",
    "priority": "normal",
    "expectedShipDate": "2026-02-10",
    "lineItems": [
      {"itemId": "item-uuid", "quantityOrdered": 2, "unitPrice": 12.50}
    ]
  }'
```

### Updating Sales Order Status

```bash
# Confirm order
curl -X PUT "http://localhost:8000/api/v1/sales-orders/{id}/status" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{"status": "confirmed"}'

# Pick items
curl -X PUT "http://localhost:8000/api/v1/sales-orders/{id}/status" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{"status": "picked"}'

# Ship order
curl -X PUT "http://localhost:8000/api/v1/sales-orders/{id}/status" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{"status": "shipped", "notes": "Tracking #123"}'

### Shipping Items

Use the ship endpoint to increment shipped quantities and transition status:

```bash
curl -X POST "http://localhost:8000/api/v1/sales-orders/{id}/ship" \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Slug: your-tenant" \
  -d '{
    "shipments": [
      {"lineItemId": "line-uuid", "quantity": 2, "fromLocationId": "loc-uuid"}
    ]
  }'
```

This will:
- Create stock movements of type `sale`
- Update `quantityShipped` on line items
- Set order status to `shipped` when all lines are fully shipped
- Write audit logs for traceability
```

### Creating a Lot

```bash
curl -X POST "http://localhost:8000/api/v1/inventory/items/{item_id}/lots" \
  -H "Content-Type: application/json" \
  -d {
    "lotNumber": "LOT-2026-001",
    "serialNumber": "SN-12345",
    "quantity": 100,
    "expirationDate": "2027-01-15",
    "manufactureDate": "2025-12-01",
    "locationId": "{warehouse_location_id}"
  }
```

### Response

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "itemId": "item-uuid-here",
    "lotNumber": "LOT-2026-001",
    "serialNumber": "SN-12345",
    "quantity": 100,
    "expirationDate": "2027-01-15",
    "manufactureDate": "2025-12-01",
    "locationId": "warehouse-uuid",
    "createdAt": "2026-01-08T10:30:00Z",
    "createdBy": "user-uuid"
  },
  "meta": {
    "timestamp": "2026-01-08T10:30:00Z",
    "requestId": "req-id-here"
  }
}
```

### Listing Lots for an Item

```bash
curl "http://localhost:8000/api/v1/inventory/items/{item_id}/lots?page=1&pageSize=25&includeExpired=false"
```

### Querying Parameters

- `page` - Page number (default: 1)
- `pageSize` - Items per page (default: 25, max: 1000)
- `locationId` - Filter by storage location
- `includeExpired` - Include expired lots (default: false)
- `orderBy` - Sort by: `created_at`, `expiration_date`, or `lot_number` (default: `created_at`)

### Updating a Lot

```bash
curl -X PUT "http://localhost:8000/api/v1/inventory/lots/{lot_id}" \
  -H "Content-Type: application/json" \
  -d {
    "quantity": 85,
    "expirationDate": "2027-02-15"
  }
```

All fields are optional for updates. Only provided fields will be modified.

### Stock Movements with Lot Tracking

When recording stock movements, you can optionally link them to a specific lot:

```bash
curl -X POST "http://localhost:8000/api/v1/stock-movements" \
  -H "Content-Type: application/json" \
  -d {
    "inventoryItemId": "{item_id}",
    "movementType": "ship",
    "quantity": 10,
    "fromLocationId": "{source_location}",
    "lotId": "{lot_id}",
    "referenceNumber": "ORDER-12345"
  }
```

### Receiving with Lots (Purchase Orders)

When receiving purchase order items, you can create multiple lots in a single request:

```bash
curl -X POST "http://localhost:8000/api/v1/purchase-orders/{po_id}/receive" \
  -H "Content-Type: application/json" \
  -d {
    "items": [
      {
        "lineItemId": "{line_item_id}",
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
    ],
    "notes": "Received from supplier ABC Corp",
    "receivedDate": "2026-01-08"
  }
```

### Lot Properties

| Property          | Type    | Required | Description                                       |
| ----------------- | ------- | -------- | ------------------------------------------------- |
| `lotNumber`       | String  | Yes      | Unique identifier for the lot (unique per tenant) |
| `serialNumber`    | String  | No       | Serial number for single-unit items               |
| `quantity`        | Integer | Yes      | Quantity of items in lot (must be > 0)            |
| `expirationDate`  | Date    | No       | Expiration date for perishable items              |
| `manufactureDate` | Date    | No       | Date item was manufactured                        |
| `locationId`      | UUID    | No       | Where the lot is physically stored                |

### Example: Complete Lot Tracking Workflow

1. **Receive items with lots:**

   - Purchase order received with 2 lots of Widget A
   - Lots created with expiration dates and locations

2. **Query available lots:**

   - Check inventory for non-expired lots of Widget A
   - Filter by location or expiration date

3. **Ship with lot traceability:**

   - Record stock movement linked to specific lot
   - Audit trail shows which lot was shipped

4. **Monitor expiration:**
   - Query approaching expiration dates
   - Schedule promotions or disposal for expiring inventory

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## Database Schema

### Inventory Items Table

| Column      | Type     | Description                 |
| ----------- | -------- | --------------------------- |
| id          | Integer  | Primary key                 |
| name        | String   | Item name                   |
| sku         | String   | Stock Keeping Unit (unique) |
| description | Text     | Item description            |
| quantity    | Integer  | Available quantity          |
| unit_price  | Float    | Price per unit              |
| category    | String   | Item category               |
| location    | String   | Storage location            |
| created_at  | DateTime | Creation timestamp          |
| updated_at  | DateTime | Last update timestamp       |

## Environment Variables

### Backend (.env)

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=synkventory
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
