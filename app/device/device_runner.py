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
    
    # Use DirectShow backend on Windows, it often fixes MSMF errors with external webcams
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
    if not cap.isOpened():
        print(f"[ERROR] Camera {camera_index} not found! Trying default camera 0...")
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("[ERROR] No camera could be opened!")
            return

    # HD Resolution (Camera will auto-adjust to its nearest supported resolution if 720p is unavailable)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    print("[SUCCESS] Camera ready. Press 'c' to capture, 'q' to quit.")

    failed_frames = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                failed_frames += 1
                if failed_frames > 30:
                    print("[ERROR] Lost connection to camera (too many failed frames).")
                    break
                time.sleep(0.1)
                continue
                
            failed_frames = 0 # Reset on success
            
            cv2.imshow("Smart Entry System", frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                print("\n[CAPTURE] Starting 3 second countdown...")
                
                countdown_start = time.time()
                capture_frame = None
                
                while True:
                    ret, current_frame = cap.read()
                    if not ret: continue
                    
                    elapsed = time.time() - countdown_start
                    remaining = 3 - int(elapsed)
                    
                    if remaining <= 0:
                        capture_frame = current_frame.copy()
                        break
                    
                    # Draw a solid rectangle and counter on the top right corner
                    display_frame = current_frame.copy()
                    h, w, _ = display_frame.shape
                    
                    rect_w, rect_h = 100, 100
                    top_x, top_y = w - rect_w - 20, 20
                    bottom_x, bottom_y = w - 20, 120
                    
                    # Solid primary color (BGR format: ~Teal)
                    cv2.rectangle(display_frame, (top_x, top_y), (bottom_x, bottom_y), (136, 148, 13), -1)
                    
                    # Add countdown text
                    text = str(remaining)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    text_size = cv2.getTextSize(text, font, 2.5, 5)[0]
                    text_x = top_x + (rect_w - text_size[0]) // 2
                    text_y = top_y + (rect_h + text_size[1]) // 2
                    
                    cv2.putText(display_frame, text, (text_x, text_y), font, 2.5, (255, 255, 255), 5, cv2.LINE_AA)
                    
                    cv2.imshow("Smart Entry System", display_frame)
                    cv2.waitKey(1)
                    
                print("\n[CAPTURE] Processing...")
                
                # Setup Date Folder
                date_str = datetime.now().strftime("%d-%m-%Y")
                base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
                photo_dir = os.path.join(base_dir, "data", "photos", date_str)
                os.makedirs(photo_dir, exist_ok=True)
                
                image_path = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
                cv2.imwrite(image_path, capture_frame)
                
                # Detect Plate
                print("[DETECTING] Reading Plate...")
                plate_number = None
                if HAS_LOCAL_ANPR:
                    plate_number = detect_plate_local(image_path)
                if not plate_number:
                    plate_number = detect_plate_api(image_path)
                
                if not plate_number:
                    print("[ERROR] Could not read plate. Try again.")
                    continue
                
                if process_vehicle(plate_number, image_path):
                    # Pause for form if AUTO_OPEN is True
                    print("[PAUSE] Camera paused. Resume in 30s or after submission.")
                    cap.release()
                    cv2.destroyAllWindows()
                    
                    # Wait logic
                    start_wait = time.time()
                    while time.time() - start_wait < FORM_TIMEOUT:
                        try:
                            # Poll for submission
                            check_resp = requests.get(f"{API_BASE_URL}/api/vehicle/{plate_number}", timeout=2)
                            if check_resp.status_code == 200:
                                data = check_resp.json()
                                if data.get('entries') and (data['entries'][0].get('visitor_name')):
                                    print("\n[SUCCESS] Form submitted!")
                                    break
                        except: pass
                        time.sleep(2)
                        print(".", end="", flush=True)
                    
                    print("\n[RESUME] Re-starting camera...")
                    # Use V4L2 backend for Linux/Pi stability
                    cap = cv2.VideoCapture(camera_index, cv2.CAP_V4L2)
                    
                    if not cap.isOpened():
                        # Fallback to default backend if V4L2 fails
                        cap = cv2.VideoCapture(camera_index)
                        
                    if not cap.isOpened():
                        print(f"[ERROR] Camera not found at index {camera_index}!")
                        return

                    # Try setting HD, but don't crash if it fails
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                    
                    # Check if we actually got a frame
                    ret, test_frame = cap.read()
                    if not ret:
                        print("[WARNING] Could not read frame. Trying lower resolution...")
                        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

            elif key == ord('q'):
                break
    finally:
        if cap:
            cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run_device_workflow()
