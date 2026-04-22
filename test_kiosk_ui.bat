@echo off
echo ========================================
echo  Kiosk UI Testing Mode
echo ========================================
echo.
echo [1/2] Starting Backend Server...
echo Server will be available at: http://localhost:8000
echo.

REM Start backend server in a new window
start "Backend Server" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo [2/2] Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo Opening Kiosk Login Page in browser...
echo Plate: TEST1234
echo.

REM Open kiosk page with a test plate number
start http://localhost:8000/api/kiosk?plate=TEST1234

echo.
echo ========================================
echo  Ready! 
echo  You can now test the ID scanning 
echo  and auto-fill on the web page.
echo ========================================
echo.
pause
