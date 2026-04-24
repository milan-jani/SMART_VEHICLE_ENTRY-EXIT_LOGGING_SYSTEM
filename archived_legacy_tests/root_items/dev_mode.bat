@echo off
REM Development Mode - Backend Only with Auto-Reload
REM Perfect for working on dashboard, UI, and API changes

echo ========================================
echo  Development Mode - Backend Only
echo ========================================
echo.
echo This mode starts ONLY the backend server
echo with auto-reload for instant updates.
echo.
echo Perfect for:
echo  - Working on dashboard UI
echo  - Testing with existing data
echo  - Making code changes
echo.
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting Backend Server with Auto-Reload...
echo.
echo  Dashboard: http://localhost:8000/api/dashboard
echo  API Docs:  http://localhost:8000/docs
echo  Entry Form: http://localhost:8000/api/form
echo.
echo The server will automatically reload when you save changes!
echo Press Ctrl+C to stop the server.
echo.
echo ========================================
echo.

REM Wait 2 seconds then open dashboard
timeout /t 2 /nobreak >nul
start http://localhost:8000/api/dashboard

REM Start server with auto-reload
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
