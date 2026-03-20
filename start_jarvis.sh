#!/bin/bash
# ==========================================================
# JARVIS v11.0 GENESIS - Linux/Mac Startup Script
# PhD-Level Fixes Applied
# ==========================================================

echo "========================================"
echo "JARVIS v11.0 GENESIS - Unified Launcher"
echo "PhD-Level System Orchestration"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org/"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js is not installed"
    echo "Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "[WARNING] .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo ""
    echo "[ACTION REQUIRED] Please edit .env and add your GROQ_API_KEY"
    echo "Then run this script again."
    exit 1
fi

# Check if GROQ_API_KEY is set
if grep -q "GROQ_API_KEY=your_groq_api_key_here" .env; then
    echo "[ERROR] GROQ_API_KEY not configured in .env"
    echo "Please edit .env and add your GROQ API key"
    echo "Get your key from: https://console.groq.com/keys"
    exit 1
fi

# Create logs directory
mkdir -p logs

echo "[1/3] Checking Python dependencies..."
if ! python3 -c "import grpc" &> /dev/null; then
    echo "Installing Python dependencies..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Python dependencies"
        exit 1
    fi
fi

echo "[2/3] Checking Node.js dependencies..."
if [ ! -d node_modules ]; then
    echo "Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to install Node.js dependencies"
        exit 1
    fi
fi

echo "[3/3] Checking gRPC protobuf files..."
if [ ! -f grpc/jarvis_pb2.py ]; then
    echo "Generating gRPC protobuf files..."
    python3 -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto
    if [ $? -ne 0 ]; then
        echo "[ERROR] Failed to generate protobuf files"
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "All checks passed!"
echo "Starting JARVIS v11.0 GENESIS..."
echo "========================================"
echo ""
echo "Services will start in order:"
echo "  1. gRPC Server (port 50051)"
echo "  2. Main Orchestrator (port 8000)"
echo "  3. WhatsApp Bridge (port 3000)"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Start unified launcher
python3 unified_launcher.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] JARVIS failed to start"
    echo "Check logs/unified_launcher.log for details"
    exit 1
fi
