import cv2
import os
import time
import requests
import json
from datetime import datetime
from config import (
    DEFAULT_CAMERA_INDEX, 
    CAPTURE_KEY, 
    QUIT_KEY, 
    API_BASE_URL,
    ANPR_MODE
)
from anpr import detect_plate

def process_vehicle(plate_number, image_path):
    """Sends detection to backend and waits for registration."""
    if not plate_number:
        print("[ERROR] Could not read plate. Try again.")
        return False

    print(f"[API] Sending {plate_number} to {API_BASE_URL}...")
    payload = {
        "vehicle_no": plate_number,
        "image_path": image_path
    }
    
    try:
        resp = requests.post(f"{API_BASE_URL}/api/new-entry", json=payload, timeout=10)
        data = resp.json()
        
        if data.get("status") == "success":
            print(f"[SUCCESS] New entry created for {plate_number}")
            return True
        elif data.get("status") == "warning":
            print(f"[UPDATE] {data.get('message')}")
            return True
        else:
            print(f"[BACKEND ERROR] {data.get('message')}")
            return False
    except Exception as e:
        print(f"[CONNECTION ERROR] Could not reach backend: {e}")
        return False

def run_device_workflow():
    # Use V4L2 for Linux/Pi
    cap = cv2.VideoCapture(DEFAULT_CAMERA_INDEX, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        print(f"[ERROR] Camera {DEFAULT_CAMERA_INDEX} not found! Trying default...")
        cap = cv2.VideoCapture(0)

    # Set lower resolution for Pi performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    print("\n" + "="*60)
    print("HYBRID LOGGING SYSTEM - CONTINUOUS MONITORING")
    print("="*60)
    print(f"[SUCCESS] Camera ready (Index: {DEFAULT_CAMERA_INDEX})")
    print(f"[INFO] Press '{CAPTURE_KEY}' to capture, '{QUIT_KEY}' to quit.\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to grab frame.")
            break

        # Display preview
        cv2.imshow("Smart Gate - Camera Feed", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord(QUIT_KEY):
            break
            
        if key == ord(CAPTURE_KEY):
            print("\n[CAPTURE] Image saved. Starting detection...")
            
            # Ensure directory exists
            os.makedirs("data/captures", exist_ok=True)
            image_path = f"data/captures/detect_{int(time.time())}.jpg"
            cv2.imwrite(image_path, frame)
            
            try:
                print("[DETECTING] Analyzing plate...")
                plate_number = detect_plate(image_path)
                
                if plate_number:
                    print(f"[DETECTED] Plate: {plate_number}")
                    if process_vehicle(plate_number, image_path):
                        print("[PAUSE] Vehicle detected. Waiting for UI registration...")
                        # Wait for user to see the success before resuming
                        time.sleep(2)
                    else:
                        print("[RETRY] Detection failed to process.")
                else:
                    print("[FAILED] Plate reader returned nothing. Check your API Key or connection.")
            except Exception as e:
                print(f"[CRITICAL ERROR] ANPR failed: {e}")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_device_workflow()
