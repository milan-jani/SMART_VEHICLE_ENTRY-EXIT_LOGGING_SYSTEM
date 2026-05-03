"""
Device Runner
Main workflow for device operation: capture, detect, and communicate with API
"""
import requests
import webbrowser
import os
import time
from datetime import datetime
from typing import Optional

# Setup base directory for imports
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.append(project_root)

from app.device.camera import capture_with_preview
from app.device.anpr import detect_plate_from_image as detect_plate_api

# Safe import for Local ANPR
try:
    from app.device.anpr_local import detect_plate_from_image as detect_plate_local
    HAS_LOCAL_ANPR = True
except (ImportError, ModuleNotFoundError):
    print("[INFO] Local ANPR not available. Using Cloud API only.")
    detect_plate_local = None
    HAS_LOCAL_ANPR = False

from app.device.config import (
    DEFAULT_CAMERA_INDEX,
    ANPR_MODE,
    API_NEW_ENTRY,
    API_UPDATE_EXIT,
    API_FORM_URL,
    API_KIOSK_URL,
    AUTO_OPEN_FORM,
    API_BASE_URL,
    FORM_TIMEOUT
)

def send_new_entry(vehicle_no: str, image_path: str) -> dict:
    try:
        in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {
            "vehicle_no": vehicle_no,
            "image_path": image_path,
            "in_time": in_time
        }
        response = requests.post(API_NEW_ENTRY, json=payload, timeout=10)
        if response.status_code == 200:
            return response.json()
        return {'success': False, 'status': 'error'}
    except Exception as e:
        print(f"[ERROR] API Connection failed: {e}")
        return {'success': False, 'status': 'error'}

def send_exit_update(vehicle_no: str) -> bool:
    try:
        out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        payload = {"vehicle_no": vehicle_no, "out_time": out_time}
        response = requests.post(API_UPDATE_EXIT, json=payload, timeout=10)
        return response.status_code == 200
    except:
        return False

def process_vehicle(plate_number: str, image_path: str) -> bool:
    print(f"\n[SUCCESS] Plate detected: {plate_number}")
    entry_result = send_new_entry(plate_number, image_path)
    
    status = entry_result.get('status', 'error')
    
    if status == 'new':
        print(f"[NEW ENTRY] Visitor marked as INSIDE")
        if AUTO_OPEN_FORM:
            print(f"[BROWSER] Opening form: {API_KIOSK_URL}?plate={plate_number}")
            # Try to open browser on host
            webbrowser.open(f"{API_KIOSK_URL}?plate={plate_number}")
            return True # Signal to pause for form
        return False
    
    elif status == 'existing' or status == 'warning':
        print(f"[UPDATE] Vehicle already inside. Marking as EXIT...")
        if send_exit_update(plate_number):
            print(f"[SUCCESS] Exit recorded for {plate_number}")
        return False
        
    return False

def run_device_workflow(camera_index: int = DEFAULT_CAMERA_INDEX) -> None:
    import cv2
    
    print("\n" + "="*60)
    print("HYBRID LOGGING SYSTEM - CONTINUOUS MONITORING")
    print("="*60)
    
    # AGGRESSIVE SEARCH FOR CAMERA (Compatible with Linux/Pi)
    cap = None
    indices = [camera_index, 0, 1, 2]
    
    for idx in indices:
        print(f"[INFO] Attempting to open Camera {idx}...")
        # Use V4L2 for Pi stability
        cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
        if not cap.isOpened():
            # Fallback to default
            cap = cv2.VideoCapture(idx)
            
        if cap.isOpened():
            print(f"[SUCCESS] Camera found at index {idx}")
            camera_index = idx
            break
            
    if not cap or not cap.isOpened():
        print("[ERROR] NO CAMERA FOUND ANYWHERE! Check hardware connection.")
        return

    # Set basic resolution first to avoid power surge crashes
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    # Try to set HD if hardware supports it
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("[SUCCESS] Camera ready. Press 'c' to capture, 'q' to quit.")

    failed_frames = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                failed_frames += 1
                if failed_frames > 20:
                    print("[ERROR] Lost connection to camera.")
                    break
                continue
            
            failed_frames = 0
            cv2.imshow("Smart Entry System", frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                print("\n[CAPTURE] Processing...")
                
                # Setup Date Folder
                date_str = datetime.now().strftime("%d-%m-%Y")
                photo_dir = os.path.join(project_root, "data", "photos", date_str)
                os.makedirs(photo_dir, exist_ok=True)
                
                image_path = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
                cv2.imwrite(image_path, frame)
                
                # Detect Plate
                print("[DETECTING] Reading Plate...")
                plate_number = None
                if HAS_LOCAL_ANPR and detect_plate_local:
                    plate_number = detect_plate_local(image_path)
                if not plate_number:
                    plate_number = detect_plate_api(image_path)
                
                if not plate_number:
                    print("[ERROR] Could not read plate. Try again.")
                    continue
                
                if process_vehicle(plate_number, image_path):
                    print("[PAUSE] Camera paused. Resume after form submission.")
                    cap.release()
                    cv2.destroyAllWindows()
                    
                    # Wait logic (indefinite or long timeout)
                    start_wait = time.time()
                    while time.time() - start_wait < 300: # 5 min timeout
                        try:
                            # Poll for submission
                            check_resp = requests.get(f"{API_BASE_URL}/api/vehicle/{plate_number}", timeout=2)
                            if check_resp.status_code == 200:
                                data = check_resp.json()
                                # Logic to check if visitor data is updated in DB
                                if data.get('entries') and len(data['entries']) > 0:
                                    if data['entries'][0].get('visitor_name'):
                                        print("\n[SUCCESS] Form submission detected!")
                                        break
                        except: pass
                        time.sleep(2)
                        print(".", end="", flush=True)
                    
                    print("\n[RESUME] Re-starting camera...")
                    # Re-initialize same way
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                    if not cap.isOpened(): cap = cv2.VideoCapture(camera_index)
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

            elif key == ord('q'):
                break
    finally:
        if cap: cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run_device_workflow()
