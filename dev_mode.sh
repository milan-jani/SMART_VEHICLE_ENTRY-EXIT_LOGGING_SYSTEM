#!/bin/bash
# Development Mode - Backend Only with Auto-Reload
# Perfect for working on dashboard, UI, and API changes

echo "========================================"
echo " Development Mode - Backend Only"
echo "========================================"
echo ""
echo "This mode starts ONLY the backend server"
echo "with auto-reload for instant updates."
echo ""
echo "Perfect for:"
echo " - Working on dashboard UI"
echo " - Testing with existing data"
echo " - Making code changes"
echo ""
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    exit 1
fi

echo "Starting Backend Server with Auto-Reload..."
echo ""
echo " Dashboard: http://localhost:8000/api/dashboard"
echo " API Docs:  http://localhost:8000/docs"
echo " Entry Form: http://localhost:8000/api/form"
echo ""
echo "The server will automatically reload when you save changes!"
echo "Press Ctrl+C to stop the server."
echo ""
echo "========================================"
echo ""

# Open dashboard in browser after 2 seconds (in background)
(sleep 2 && (xdg-open http://localhost:8000/api/dashboard 2>/dev/null || open http://localhost:8000/api/dashboard 2>/dev/null)) &

# Start server with auto-reload
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
