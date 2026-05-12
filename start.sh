#!/bin/bash

echo "🚀 Starting Smart Vehicle Entry-Exit Logging System..."

# 1. Stop any existing containers
echo "Stopping existing containers..."
docker-compose down

# 2. Start Docker containers (Backend & Camera)
echo "Starting Backend and Camera Services..."
docker-compose up -d

# 3. Start IR Sensor Handler in Background
echo "Initializing IR Sensor Hardware..."
# Kill any existing IR handler first
pkill -f "hardware/ir_handler.py" || true
# Start IR handler in background and redirect logs
python3 hardware/ir_handler.py > ir_handler.log 2>&1 &
IR_PID=$!

echo "✅ System is UP!"
echo "--------------------------------------------------"
echo "Backend/Camera: Running in Docker (network: host)"
echo "IR Handler: Running on Host (PID: $IR_PID)"
echo "IR Logs: tail -f ir_handler.log"
echo "--------------------------------------------------"
echo "Press Ctrl+C to stop viewing container logs..."

# Show docker logs
docker-compose logs -f
