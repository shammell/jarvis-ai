@echo off
REM ==========================================================
REM JARVIS v11.0 GENESIS - Windows Startup Script
REM PhD-Level Fixes Applied
REM ==========================================================

echo ========================================
echo JARVIS v11.0 GENESIS - Unified Launcher
echo PhD-Level System Orchestration
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env
    echo.
    echo [ACTION REQUIRED] Please edit .env and add your GROQ_API_KEY
    echo Then run this script again.
    pause
    exit /b 1
)

REM Check if GROQ_API_KEY is set
findstr /C:"GROQ_API_KEY=your_groq_api_key_here" .env >nul
if not errorlevel 1 (
    echo [ERROR] GROQ_API_KEY not configured in .env
    echo Please edit .env and add your GROQ API key
    echo Get your key from: https://console.groq.com/keys
    pause
    exit /b 1
)

REM Create logs directory
if not exist logs mkdir logs

echo [1/3] Checking Python dependencies...
python -c "import grpc" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        pause
        exit /b 1
    )
)

echo [2/3] Checking Node.js dependencies...
if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node.js dependencies
        pause
        exit /b 1
    )
)

echo [3/3] Checking gRPC protobuf files...
if not exist grpc\jarvis_pb2.py (
    echo Generating gRPC protobuf files...
    python -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto
    if errorlevel 1 (
        echo [ERROR] Failed to generate protobuf files
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo All checks passed!
echo Starting JARVIS v11.0 GENESIS...
echo ========================================
echo.
echo Services will start in order:
echo   1. gRPC Server (port 50051)
echo   2. Main Orchestrator (port 8000)
echo   3. WhatsApp Bridge (port 3000)
echo.
echo Press Ctrl+C to stop all services
echo.

REM Start unified launcher
python unified_launcher.py

if errorlevel 1 (
    echo.
    echo [ERROR] JARVIS failed to start
    echo Check logs/unified_launcher.log for details
    pause
    exit /b 1
)

pause
