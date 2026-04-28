@echo off
title Vehicle Logging System - Device Runner
echo [DEVICE] Starting Device Workflow...
echo Press 'c' to capture, 'v' for visitor, 'q' to quit.
echo.
python -m app.device.device_runner
pause
