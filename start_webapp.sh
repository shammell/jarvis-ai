#!/bin/bash

# JARVIS Web App - Start Script
# Starts both backend and frontend in separate terminals

echo "========================================"
echo "Starting JARVIS Web App"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Run setup_webapp.sh first"
    exit 1
fi

# Check if web/.env.local exists
if [ ! -f "web/.env.local" ]; then
    echo "ERROR: web/.env.local not found!"
    echo "Run setup_webapp.sh first"
    exit 1
fi

echo "Starting backend on http://localhost:8000"
echo "Starting frontend on http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Start backend in background
python main.py &
BACKEND_PID=$!

# Wait a bit for backend to start
sleep 3

# Start frontend in background
cd web
npm run dev &
FRONTEND_PID=$!
cd ..

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

# Keep script running
wait
