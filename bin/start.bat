@echo off
REM Start the FastAPI backend server

echo Starting Hybrid Logging System Backend...
echo.
echo Backend will be available at: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo Dashboard: http://localhost:8000/api/dashboard
echo.

python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
