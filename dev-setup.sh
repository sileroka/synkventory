#!/bin/bash

# Development setup script for Synkventory
# This script sets up the development environment

echo "🚀 Setting up Synkventory development environment..."

# Check for required tools
echo "Checking for required tools..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18 or higher."
    exit 1
fi

if ! command -v docker &> /dev/null; then
    echo "⚠️  Docker is not installed. You'll need it to run PostgreSQL."
fi

echo "✅ All required tools are available"

# Setup backend
echo ""
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment and installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Update it with your configuration if needed."
fi

deactivate
cd ..

# Setup frontend
echo ""
echo "📦 Setting up frontend..."
cd frontend
echo "Installing npm dependencies..."
npm install

cd ..

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Start PostgreSQL: docker run -d --name synkventory-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=synkventory -p 5432:5432 postgres:15-alpine"
echo "2. Start backend: cd backend && source venv/bin/activate && uvicorn app.main:app --reload"
echo "3. Start frontend: cd frontend && npm start"
echo "4. Open browser: http://localhost:4200"
