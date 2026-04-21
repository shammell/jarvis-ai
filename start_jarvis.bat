@echo off
setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

if not exist logs mkdir logs
set "LOG_FILE=logs\startup.log"

echo [START] JARVIS startup >> "%LOG_FILE%"
echo [HEALTH CHECK] Checking prerequisites... >> "%LOG_FILE%"

where python >nul 2>&1
if errorlevel 1 (
  echo [ERROR] python not found >> "%LOG_FILE%"
  exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
  echo [ERROR] node not found >> "%LOG_FILE%"
  exit /b 1
)

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

python unified_launcher.py >> "%LOG_FILE%" 2>&1
exit /b %errorlevel%
