@echo off
REM ==========================================================
REM JARVIS v9.0 - Launch All Services (One Command, Windows)
REM ==========================================================
REM This batch script starts: Python gRPC server, WhatsApp Node bridge, and main orchestrator in 3 windows

setlocal enableextensions enabledelayedexpansion
cd /d %~dp0

REM Start Python gRPC server
start "JARVIS gRPC" cmd /k "python grpc_service\python_server.py"

REM Wait a bit
ping 127.0.0.1 -n 4 >nul

REM Start WhatsApp Node.js bridge
start "JARVIS WhatsApp Bridge" cmd /k "npm run start:bridge"

REM Wait a bit
ping 127.0.0.1 -n 6 >nul

REM Start Main Orchestrator (JARVIS v9.0)
start "JARVIS Main v9.0" cmd /k "python main.py"

REM This window closes automatically
exit
