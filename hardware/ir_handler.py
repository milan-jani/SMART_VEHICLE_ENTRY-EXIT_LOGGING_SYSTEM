import RPi.GPIO as GPIO
import time
import requests
import sys
import os
from dotenv import load_dotenv

# Load configuration
load_dotenv()

# GPIO Setup
IR_PIN = int(os.getenv("IR_SENSOR_PIN", 17)) # Default GPIO 17
API_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

GPIO.setmode(GPIO.BCM)
GPIO.setup(IR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

print(f"--- IR Sensor Handler Started ---")
print(f"Monitoring GPIO Pin: {IR_PIN}")
print(f"Target API: {API_URL}")

last_trigger_time = 0
DEBOUNCE_TIME = 5.0 # Seconds to wait between triggers

try:
    while True:
        # Check IR state (Active Low)
        # GPIO.input returns 0 if sensor is cut (object detected)
        if GPIO.input(IR_PIN) == GPIO.LOW:
            current_time = time.time()
            if current_time - last_trigger_time > DEBOUNCE_TIME:
                print("🚨 [IR] Sensor Cut Detected! Sending Trigger...")
                try:
                    # Notify the backend
                    requests.post(f"{API_URL}/api/ir-trigger", timeout=2)
                    last_trigger_time = current_time
                except Exception as e:
                    print(f"❌ [IR] Failed to send trigger: {e}")
        
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nStopping IR Handler...")
finally:
    GPIO.cleanup()
