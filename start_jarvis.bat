@echo off
REM ==========================================================
REM JARVIS v11.0 GENESIS - Windows Startup Script
REM PhD-Level Fixes Applied
REM ==========================================================
REM Startup Task Compatible - Sets environment and health checks

setlocal EnableDelayedExpansion

echo ========================================
echo JARVIS v11.0 GENESIS - Unified Launcher
echo PhD-Level System Orchestration
echo ========================================
echo.

REM Create logs directory first
if not exist logs mkdir logs

REM ==========================================================
REM HEALTH CHECK ON STARTUP
REM ==========================================================

echo [HEALTH CHECK] Running system health check...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://www.python.org/
    echo HEALTH_CHECK_STATUS=FAILED_PYTHON
    echo %ERRORLEVEL% > logs\health_check_status.txt
    pause
    exit /b 1
)
echo [OK] Python installed

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js 18+ from https://nodejs.org/
    echo [HEALTH_CHECK_STATUS=FAILED_NODE]
    echo %ERRORLEVEL% > logs\health_check_status.txt
    pause
    exit /b 1
)
echo [OK] Node.js installed

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found
    echo Creating .env from .env.example...
    copy .env.example .env >nul 2>&1
    echo.
    echo [ACTION REQUIRED] Please edit .env and add your GROQ_API_KEY
    echo Then run this script again.
    echo [HEALTH_CHECK_STATUS=FAILED_ENV]
    echo %ERRORLEVEL% > logs\health_check_status.txt
    pause
    exit /b 1
)
echo [OK] .env file exists

REM Check if GROQ_API_KEY is set
findstr /C:"GROQ_API_KEY=your_groq_api_key_here" .env >nul
if not errorlevel 1 (
    echo [ERROR] GROQ_API_KEY not configured in .env
    echo Please edit .env and add your GROQ API key
    echo Get your key from: https://console.groq.com/keys
    echo [HEALTH_CHECK_STATUS=FAILED_API_KEY]
    echo %ERRORLEVEL% > logs\health_check_status.txt
    pause
    exit /b 1
)
echo [OK] API key configured
echo [OK] HEALTH_CHECK_STATUS=HEALTHY
echo %ERRORLEVEL% > logs\health_check_status.txt

REM Set Python path explicitly for startup task compatibility
set PATH=%CD%\venv\Scripts;%CD%;%PATH%

REM Activate virtual environment if present
if exist venv\Scripts\activate.bat (
    echo.
    echo [VIRTUAL ENV] Activating Python virtual environment...
    call venv\Scripts\activate.bat
) else if exist env\Scripts\activate.bat (
    echo.
    echo [VIRTUAL ENV] Activating Python virtual environment...
    call env\Scripts\activate.bat
) else (
    echo.
    echo [VIRTUAL ENV] No virtual environment found, using system Python
)
echo.

REM ==========================================================
REM STARTUP SEQUENCE
REM ==========================================================

echo [1/3] Checking Python dependencies...
python -c "import grpc" >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies
        echo [HEALTH_CHECK_STATUS=FAILED_DEPS]
        echo %ERRORLEVEL% > logs\health_check_status.txt
        pause
        exit /b 1
    )
)
echo [OK] Python dependencies ready

echo [2/3] Checking Node.js dependencies...
if not exist node_modules (
    echo Installing Node.js dependencies...
    call npm install
    if errorlevel 1 (
        echo [ERROR] Failed to install Node.js dependencies
        echo [HEALTH_CHECK_STATUS=FAILED_NPM]
        echo %ERRORLEVEL% > logs\health_check_status.txt
        pause
        exit /b 1
    )
)
echo [OK] Node.js dependencies ready

echo [3/3] Checking gRPC protobuf files...
if not exist grpc_service\jarvis_pb2.py (
    echo Generating gRPC protobuf files...
    python -m grpc_tools.protoc -I./grpc_service --python_out=./grpc_service --grpc_python_out=./grpc_service ./grpc_service/jarvis.proto
    if errorlevel 1 (
        echo [ERROR] Failed to generate protobuf files
        echo [HEALTH_CHECK_STATUS=FAILED_PROTOBUF]
        echo %ERRORLEVEL% > logs\health_check_status.txt
        pause
        exit /b 1
    )
)
echo [OK] gRPC protobuf ready

echo.
echo ========================================
echo All health checks passed!
echo Starting JARVIS v11.0 GENESIS...
echo ========================================
echo.
echo Services will start in order:
echo   1. gRPC Server (port 50051)
echo   2. Main Orchestrator (port 8080)
echo   3. WhatsApp Bridge (port 3000)
echo.
echo Press Ctrl+C to stop all services
echo.

REM Start unified launcher with logging (includes voice runtime supervision)
python launchers\unified_launcher.py > logs\unified_launcher.log 2>&1

if errorlevel 1 (
    echo.
    echo [ERROR] JARVIS failed to start
    echo Check logs/unified_launcher.log for details
    echo [HEALTH_CHECK_STATUS=FAILED_LAUNCH]
    echo %ERRORLEVEL% > logs\health_check_status.txt
    pause
    exit /b 1
)

echo.
echo [OK] JARVIS services started successfully
exit /b 0
