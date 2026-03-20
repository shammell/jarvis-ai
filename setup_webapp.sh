#!/bin/bash

echo "========================================"
echo "JARVIS Web App - Quick Start"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please create .env with Supabase credentials"
    echo ""
    echo "Required variables:"
    echo "  SUPABASE_URL=your_url"
    echo "  SUPABASE_SERVICE_KEY=your_key"
    echo "  SUPABASE_JWT_SECRET=your_secret"
    echo "  CORS_ORIGINS=http://localhost:3000"
    exit 1
fi

# Check if web/.env.local exists
if [ ! -f "web/.env.local" ]; then
    echo "WARNING: web/.env.local not found!"
    echo "Creating from example..."
    cp web/.env.local.example web/.env.local
    echo "Please edit web/.env.local with your Supabase credentials"
    echo ""
fi

# Install backend dependencies
echo "Installing backend dependencies..."
pip install supabase pyjwt

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd web
npm install
cd ..

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Run database migrations in Supabase SQL Editor"
echo "   File: supabase/migrations/20260309_create_chat_tables.sql"
echo ""
echo "2. Start backend (Terminal 1):"
echo "   python main.py"
echo ""
echo "3. Start frontend (Terminal 2):"
echo "   cd web && npm run dev"
echo ""
echo "4. Open http://localhost:3000"
echo ""
