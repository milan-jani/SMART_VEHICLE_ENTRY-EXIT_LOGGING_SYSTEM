@echo off
REM Unified Startup Script for Hybrid Logging System
REM This script starts both backend server and device workflow

echo ========================================
echo  Hybrid Logging System - Unified Start
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

echo [1/3] Checking dependencies...
python -c "import fastapi, uvicorn, cv2" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Some dependencies missing. Installing...
    pip install -r requirements.txt
)

echo.
echo [2/3] Starting Backend Server...
echo Server will be available at: http://localhost:8000
echo.
start "Backend Server" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

REM Wait for server to start
timeout /t 3 /nobreak >nul

echo [3/3] Starting Device Workflow...
echo Press 'c' to capture, 'q' to quit
echo.
start "Device Workflow" cmd /k "python -m app.device.device_runner"

echo.
echo ========================================
echo  System Started Successfully!
echo ========================================
echo.
echo  Backend Server: http://localhost:8000
echo  Dashboard: http://localhost:8000/api/dashboard
echo  API Docs: http://localhost:8000/docs
echo.
echo  Two new windows opened:
echo   1. Backend Server
echo   2. Device Workflow (Camera)
echo.
echo Press any key to open dashboard in browser...
pause >nul

REM Open dashboard in default browser
start http://localhost:8000/api/dashboard

echo.
echo To stop the system, close both terminal windows.
echo.
