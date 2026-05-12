import RPi.GPIO as GPIO
import time
import requests
import os
from dotenv import load_dotenv

# Load configuration
load_dotenv()

# GPIO Setup
IR_PIN = int(os.getenv("IR_SENSOR_PIN", 17)) # Default GPIO 17
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
DEBOUNCE_TIME = 5000 # Milliseconds (5 seconds)

def ir_callback(channel):
    """Callback function triggered on IR sensor edge detection."""
    print("🚨 [IR] Interrupt Triggered! Sensor Cut Detected.")
    try:
        # Notify the backend
        requests.post(f"{API_URL}/api/ir-trigger", timeout=2)
        print("✅ [IR] Trigger signal sent to API.")
    except Exception as e:
        print(f"❌ [IR] Failed to send trigger: {e}")

# GPIO Initialization
GPIO.setmode(GPIO.BCM)
# Using PULL_UP because most IR sensors are Active-Low
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Add Interrupt Event Detection (Falling edge = Sensor cut)
# bouncetime handles hardware debounce
GPIO.add_event_detect(IR_PIN, GPIO.FALLING, callback=ir_callback, bouncetime=DEBOUNCE_TIME)

print(f"--- IR Interrupt Handler Started ---")
print(f"Monitoring GPIO Pin: {IR_PIN} (Interrupt Mode)")
print(f"Target API: {API_URL}")
print("Press Ctrl+C to exit.")

try:
    # Keep the script alive with minimal CPU usage
    while True:
        time.sleep(10) # Sleep for long periods, interrupts work in background

except KeyboardInterrupt:
    print("\nStopping IR Handler...")
finally:
    GPIO.cleanup()
    print("GPIO Cleanup done.")
