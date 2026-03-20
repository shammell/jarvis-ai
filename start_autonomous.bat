@echo off
REM ==========================================================
REM JARVIS v9.0 - Autonomous Mode Launcher
REM Starts JARVIS in fully autonomous mode
REM No user interaction needed - runs automatically
REM ==========================================================

echo ============================================================
echo JARVIS v9.0 - AUTONOMOUS MODE
echo ============================================================
echo.
echo Starting JARVIS in fully autonomous mode...
echo System will auto-resume, auto-execute, and self-optimize
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

cd /d "%~dp0"

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Create data directory if it doesn't exist
if not exist "data" mkdir data

REM Start JARVIS in autonomous mode
python jarvis_autonomous.py

pause
