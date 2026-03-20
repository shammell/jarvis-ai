#!/bin/bash
# ==========================================================
# JARVIS v9.0 - Launch All Services (One Command)
# ==========================================================
# This script launches: Python gRPC server, WhatsApp Node.js bridge, and the main JARVIS orchestrator

set -e
trap 'kill $(jobs -p) &>/dev/null' EXIT

cd "$(dirname "$0")"

# Start Python gRPC server (background)
echo "[1/3] Starting gRPC server ..."
python grpc/python_server.py &
GRPC_PID=$!
sleep 3

# Start WhatsApp Node.js bridge (background)
echo "[2/3] Starting WhatsApp bridge ..."
npm run start:bridge &
BRIDGE_PID=$!
sleep 5

# Start main JARVIS v9.0 orchestrator (foreground)
echo "[3/3] Starting main JARVIS v9.0 orchestrator... (press Ctrl+C to stop all)"
python main.py

# When main orchestrator exits, kill all background children
echo "Shutting down background services..."
kill $GRPC_PID $BRIDGE_PID &>/dev/null || true
echo "Done. All JARVIS services shut down."
