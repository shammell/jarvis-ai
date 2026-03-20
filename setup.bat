@echo off
REM ==========================================================
REM JARVIS v9.0 ULTRA - Quick Start Script (Windows)
REM ==========================================================

echo ==================================
echo JARVIS v9.0 ULTRA - Quick Start
echo ==================================

REM Check Python
echo.
echo Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.10+
    exit /b 1
)
echo [OK] Python found

REM Check Node.js
echo.
echo Checking Node.js...
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    exit /b 1
)
echo [OK] Node.js found

REM Create directories
echo.
echo Creating directories...
if not exist logs mkdir logs
if not exist state mkdir state
if not exist memory_storage mkdir memory_storage
if not exist models\lora_adapters mkdir models\lora_adapters
echo [OK] Directories created

REM Check .env file
echo.
echo Checking environment configuration...
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    copy .env.example .env
    echo [WARNING] Please edit .env and add your GROQ_API_KEY
    echo [WARNING] Get your key from: https://console.groq.com/keys
) else (
    echo [OK] .env file exists
)

REM Install Python dependencies
echo.
echo Installing Python dependencies...
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
echo [OK] Python dependencies installed

REM Install Node.js dependencies
echo.
echo Installing Node.js dependencies...
call npm install >nul 2>&1
echo [OK] Node.js dependencies installed

REM Generate gRPC code
echo.
echo Generating gRPC code...
python -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] gRPC code generated
) else (
    echo [WARNING] gRPC code generation skipped
)

REM Summary
echo.
echo ==================================
echo [OK] JARVIS v9.0 ULTRA Setup Complete!
echo ==================================
echo.
echo Next Steps:
echo 1. Edit .env file with your API keys
echo 2. Start services in separate terminals:
echo    Terminal 1: python grpc\python_server.py
echo    Terminal 2: npm run start:bridge
echo    Terminal 3: python main.py
echo.
echo 3. Test the system:
echo    curl http://localhost:8000/health
echo.
echo 4. View documentation:
echo    type README.md
echo.
echo For detailed setup, see README.md
echo.

pause
