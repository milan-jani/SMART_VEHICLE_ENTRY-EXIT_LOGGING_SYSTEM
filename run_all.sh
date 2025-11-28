#!/bin/bash
# Unified Startup Script for Hybrid Logging System
# This script starts both backend server and device workflow

echo "========================================"
echo " Hybrid Logging System - Unified Start"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    echo "Please install Python 3.11+ and try again"
    exit 1
fi

echo "[1/3] Checking dependencies..."
python3 -c "import fastapi, uvicorn, cv2" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "WARNING: Some dependencies missing. Installing..."
    pip3 install -r requirements.txt
fi

echo ""
echo "[2/3] Starting Backend Server..."
echo "Server will be available at: http://localhost:8000"
echo ""

# Start backend in background
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# Wait for server to start
sleep 3

echo "[3/3] Starting Device Workflow..."
echo "Press 'c' to capture, 'q' to quit"
echo ""

# Start device workflow in background
python3 -m app.device.device_runner &
DEVICE_PID=$!

echo ""
echo "========================================"
echo " System Started Successfully!"
echo "========================================"
echo ""
echo "  Backend Server: http://localhost:8000"
echo "  Dashboard: http://localhost:8000/api/dashboard"
echo "  API Docs: http://localhost:8000/docs"
echo ""
echo "  Backend PID: $BACKEND_PID"
echo "  Device PID: $DEVICE_PID"
echo ""

# Open dashboard in default browser (works on most Linux/Mac systems)
if command -v xdg-open &> /dev/null; then
    sleep 2
    xdg-open http://localhost:8000/api/dashboard &
elif command -v open &> /dev/null; then
    sleep 2
    open http://localhost:8000/api/dashboard &
fi

echo "Press Ctrl+C to stop all services..."
echo ""

# Wait for interrupt
trap "echo ''; echo 'Stopping services...'; kill $BACKEND_PID $DEVICE_PID 2>/dev/null; echo 'All services stopped.'; exit 0" INT

# Keep script running
wait
