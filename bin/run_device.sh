#!/bin/bash
# Run the device workflow

echo "Starting Device Workflow..."
echo ""
echo "Press 'c' to capture image"
echo "Press 'q' to quit"
echo ""
echo "Make sure backend server is running first!"
echo "(Run start.sh in another terminal)"
echo ""

python -m app.device.device_runner
