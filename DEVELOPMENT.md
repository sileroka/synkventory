# Development Guide

This guide provides detailed instructions for developing Synkventory.

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Docker and Docker Compose
- Git

## Quick Start

### Option 1: Using Docker Compose (Recommended for Testing)

The easiest way to get started:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

Access the application:
- Frontend: http://localhost
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Local Development

For active development with hot-reload:

1. **Run the setup script:**
```bash
./dev-setup.sh
```

2. **Start PostgreSQL:**
```bash
docker run -d \
  --name synkventory-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=synkventory \
  -p 5432:5432 \
  postgres:15-alpine
```

3. **Start the backend (in a new terminal):**
```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
uvicorn app.main:app --reload
```

Backend will be available at http://localhost:8000

4. **Start the frontend (in another terminal):**
```bash
cd frontend
npm start
```

Frontend will be available at http://localhost:4200

## Project Structure

```
synkventory/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   │   └── v1/
│   │   │       ├── api.py     # API router aggregation
│   │   │       └── inventory.py  # Inventory endpoints
│   │   ├── core/              # Core configuration
│   │   │   └── config.py      # Settings and environment
│   │   ├── db/                # Database configuration
│   │   │   └── session.py     # DB session management
│   │   ├── models/            # SQLAlchemy models
│   │   │   └── inventory.py  # Inventory data model
│   │   ├── schemas/           # Pydantic schemas
│   │   │   └── inventory.py  # Inventory request/response schemas
│   │   └── main.py            # Application entry point
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # Angular components
│   │   │   │   └── inventory-list/  # Main inventory UI
│   │   │   ├── models/        # TypeScript interfaces
│   │   │   │   └── inventory-item.model.ts
│   │   │   ├── services/      # API services
│   │   │   │   └── inventory.service.ts
│   │   │   ├── app.component.*  # Root component
│   │   │   ├── app.config.ts  # App configuration
│   │   │   └── app.routes.ts  # Routing configuration
│   │   ├── styles.scss        # Global styles with PrimeNG
│   │   └── index.html         # HTML entry point
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── angular.json
│   └── package.json
│
├── docker-compose.yml         # Docker orchestration
├── dev-setup.sh              # Development setup script
├── DEVELOPMENT.md            # This file
└── README.md                 # Main documentation
```

## Backend Development

### Adding New API Endpoints

1. Create a model in `backend/app/models/`
2. Create schemas in `backend/app/schemas/`
3. Create endpoints in `backend/app/api/v1/`
4. Register the router in `backend/app/api/v1/api.py`

Example:
```python
# models/category.py
from sqlalchemy import Column, Integer, String
from app.db.session import Base

class Category(Base):
    __tablename__ = "categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

# schemas/category.py
from pydantic import BaseModel

class CategoryCreate(BaseModel):
    name: str

class Category(CategoryCreate):
    id: int
    class Config:
        from_attributes = True

# api/v1/category.py
from fastapi import APIRouter
router = APIRouter()

@router.get("/")
def get_categories():
    # Implementation
    pass

# api/v1/api.py
from app.api.v1 import inventory, category
api_router.include_router(category.router, prefix="/categories", tags=["categories"])
```

### Database Migrations

The app currently uses automatic table creation on startup. For production, consider using Alembic:

```bash
cd backend
source venv/bin/activate

# Initialize Alembic (one time)
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
```

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest  # After adding tests
```

## Frontend Development

### Adding New Components

```bash
cd frontend
ng generate component components/my-component
```

### Adding New Services

```bash
cd frontend
ng generate service services/my-service
```

### PrimeNG Components

The project uses PrimeNG UI components. Available components:
- Table (p-table)
- Button (p-button)
- Dialog (p-dialog)
- Input (pInputText, p-inputNumber, pInputTextarea)
- Toast notifications (p-toast)
- Confirm dialog (p-confirmDialog)

See [PrimeNG documentation](https://primeng.org/) for more components.

### Building for Production

```bash
cd frontend
npm run build
```

Build output will be in `dist/frontend/`.

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

### Backend (.env)

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_SERVER=localhost  # Use 'db' when running in Docker
POSTGRES_PORT=5432
POSTGRES_DB=synkventory
API_V1_STR=/api/v1
PROJECT_NAME=Synkventory API
```

### Frontend

To change the API URL, edit `frontend/src/app/services/inventory.service.ts`:
```typescript
private apiUrl = 'http://localhost:8000/api/v1/inventory';
```

For production, use environment files in `frontend/src/environments/`.

## Database Schema

### Inventory Items

| Column      | Type      | Description                    |
|-------------|-----------|--------------------------------|
| id          | Integer   | Primary key                    |
| name        | String    | Item name (required)           |
| sku         | String    | Stock Keeping Unit (unique)    |
| description | Text      | Item description               |
| quantity    | Integer   | Available quantity (default: 0)|
| unit_price  | Float     | Price per unit (default: 0.0)  |
| category    | String    | Item category                  |
| location    | String    | Storage location               |
| created_at  | DateTime  | Creation timestamp             |
| updated_at  | DateTime  | Last update timestamp          |

## Troubleshooting

### Backend Issues

**Issue**: Can't connect to database
```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# View PostgreSQL logs
docker logs synkventory-postgres
```

**Issue**: Import errors
```bash
# Reinstall dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend Issues

**Issue**: Build errors
```bash
# Clear node_modules and reinstall
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue**: CORS errors
- Ensure backend is configured with correct CORS origins in `backend/app/core/config.py`
- Check that the frontend is accessing the correct API URL

### Docker Issues

**Issue**: Port already in use
```bash
# Find process using the port
lsof -i :8000  # or :80, :5432

# Stop existing containers
docker-compose down
```

**Issue**: Database connection refused
```bash
# Wait for database to be ready
docker-compose logs db

# Restart backend container
docker-compose restart backend
```

## Code Style

### Backend (Python)
- Follow PEP 8
- Use type hints
- Document functions with docstrings

### Frontend (TypeScript)
- Follow Angular style guide
- Use strict typing
- Component files should be focused and concise

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test your changes
5. Submit a pull request

## Next Steps

- [ ] Add authentication and user management
- [ ] Implement role-based access control
- [ ] Add search and filtering
- [ ] Create reports and analytics
- [ ] Add barcode scanning support
- [ ] Implement audit logs
- [ ] Add email notifications
- [ ] Create mobile-responsive design improvements
