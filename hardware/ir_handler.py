from gpiozero import Button
from signal import pause
import requests
import os
import time
from dotenv import load_dotenv

# Load configuration
load_dotenv()

# GPIO Setup
# gpiozero uses BCM numbering by default
IR_PIN = int(os.getenv("IR_SENSOR_PIN", 17)) 
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEBOUNCE_TIME = 5.0 # Seconds

# Initialize IR Sensor as a "Button"
# pull_up=True because most IR sensors are Active-Low (Low when cut)
sensor = Button(IR_PIN, pull_up=True, bounce_time=0.1)

last_trigger_time = 0

def ir_triggered():
    """Function called when IR sensor is cut (Pressed)."""
    global last_trigger_time
    current_time = time.time()
    
    # Custom debounce for 5 seconds
    if current_time - last_trigger_time > DEBOUNCE_TIME:
        print("🚨 [IR] Sensor Cut Detected! (Interrupt via gpiozero)")
        try:
            requests.post(f"{API_URL}/api/ir-trigger", timeout=2)
            print("✅ [IR] Trigger signal sent to API.")
            last_trigger_time = current_time
        except Exception as e:
            print(f"❌ [IR] Failed to send trigger: {e}")

# Assign the function to the 'when_pressed' event (Falling edge)
sensor.when_pressed = ir_triggered

print(f"--- IR Universal Handler Started (gpiozero) ---")
print(f"Monitoring GPIO Pin: {IR_PIN}")
print(f"Target API: {API_URL}")
print("System is idle and waiting for interrupts... (CPU usage < 1%)")

# Keep the script running
pause()
