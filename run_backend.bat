@echo off
title Vehicle Logging System - Backend Server
echo [BACKEND] Starting FastAPI Server...
echo API Documentation: http://localhost:8000/docs
echo.
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pause
