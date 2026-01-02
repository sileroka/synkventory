# Synkventory

A modern web-based inventory management system built with Python/FastAPI backend, Angular/PrimeNG frontend, and PostgreSQL database.

## Tech Stack

- **Backend**: Python 3.11+ with FastAPI
- **Frontend**: Angular 17 with PrimeNG UI components
- **Database**: PostgreSQL 15
- **Containerization**: Docker & Docker Compose

## Features

- ✅ Complete CRUD operations for inventory items
- ✅ RESTful API with automatic documentation (Swagger/OpenAPI)
- ✅ Modern, responsive UI with PrimeNG components
- ✅ PostgreSQL database for reliable data storage
- ✅ Dockerized deployment for easy setup
- ✅ CORS enabled for frontend-backend communication

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

### Health Check

- `GET /health` - Health check endpoint

## API Documentation

Once the backend is running, visit http://localhost:8000/docs for interactive API documentation powered by Swagger UI.

## Database Schema

### Inventory Items Table

| Column      | Type      | Description                    |
|-------------|-----------|--------------------------------|
| id          | Integer   | Primary key                    |
| name        | String    | Item name                      |
| sku         | String    | Stock Keeping Unit (unique)    |
| description | Text      | Item description               |
| quantity    | Integer   | Available quantity             |
| unit_price  | Float     | Price per unit                 |
| category    | String    | Item category                  |
| location    | String    | Storage location               |
| created_at  | DateTime  | Creation timestamp             |
| updated_at  | DateTime  | Last update timestamp          |

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
