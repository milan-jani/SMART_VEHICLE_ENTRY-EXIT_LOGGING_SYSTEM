import cv2
import os
import time
import requests
import platform
from datetime import datetime

try:
    from .config import DEFAULT_CAMERA_INDEX, CAPTURE_KEY, QUIT_KEY, API_BASE_URL, ANPR_MODE
    from .anpr import detect_plate
except (ImportError, ValueError):
    from config import DEFAULT_CAMERA_INDEX, CAPTURE_KEY, QUIT_KEY, API_BASE_URL, ANPR_MODE
    from anpr import detect_plate

IS_WINDOWS = platform.system() == "Windows"

def check_kiosk_status():
    """Returns True if system is ready for next vehicle."""
    try:
        # Use very short timeout for local polling to avoid stuttering
        r = requests.get(f"{API_BASE_URL}/api/kiosk-status", timeout=0.5)
        return r.status_code == 200 and r.json().get("status") == "ready"
    except:
        return False

def process_vehicle(plate_number, image_path):
    """Sends detection to backend."""
    if not plate_number:
        print("[ERROR] Could not read plate. Try again.", flush=True)
        return False

    print(f"[API] Sending {plate_number} to {API_BASE_URL}...", flush=True)
    payload = {"vehicle_no": plate_number, "image_path": image_path}
    
    try:
        resp = requests.post(f"{API_BASE_URL}/api/new-entry", json=payload, timeout=10)
        data = resp.json()
        
        status = data.get("status")
        if status in ("success", "new", "worker_entry"):
            print(f"[SUCCESS] {data.get('message')}", flush=True)
            return "handover"
        elif status == "warning":
            # Vehicle is already inside, this is likely an EXIT
            print(f"[UPDATE] {data.get('message')}. Registering EXIT...", flush=True)
            exit_resp = requests.post(f"{API_BASE_URL}/api/update-exit", json={"vehicle_no": plate_number}, timeout=10)
            if exit_resp.ok:
                print(f"[EXIT] Vehicle {plate_number} has exited successfully.", flush=True)
                return "exit"
            else:
                print(f"[ERROR] Failed to update exit: {exit_resp.text}", flush=True)
                return "fail"
        else:
            print(f"[BACKEND ERROR] {data.get('message')}", flush=True)
            return "fail"
    except Exception as e:
        print(f"[CONNECTION ERROR] Could not reach backend: {e}", flush=True)
        return "fail"

def open_camera(index):
    """Opens camera with OS-appropriate backend."""
    if IS_WINDOWS:
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
    
    if not cap.isOpened():
        cap = cv2.VideoCapture(index)
    
    if not cap.isOpened() and index != 0:
        print(f"[WARN] Camera {index} failed, trying 0...", flush=True)
        cap = cv2.VideoCapture(0)
    
    return cap

def run_device_workflow():
    print("\n" + "="*60)
    print("HYBRID LOGGING SYSTEM - LAPTOP MODE")
    print("="*60)
    print(f"[INFO] Camera Index: {DEFAULT_CAMERA_INDEX}")
    print(f"[INFO] Press '{CAPTURE_KEY}' to capture, '{QUIT_KEY}' to quit.\n", flush=True)

    while True:
        cap = open_camera(DEFAULT_CAMERA_INDEX)
        
        if not cap.isOpened():
            print("[FATAL] No camera found. Exiting.", flush=True)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print("[READY] Camera feed active. Waiting for captures...\n", flush=True)
        
        last_kiosk_check = 0
        kiosk_ready = True

        while True:
            ret, frame = cap.read()
            if not ret:
                print("[ERROR] Lost camera feed.", flush=True)
                break

            # Update kiosk status every 2 seconds without blocking too much
            # (Note: requests is still sync, but doing it here keeps the 'c' press instant)
            if time.time() - last_kiosk_check > 2:
                kiosk_ready = check_kiosk_status()
                last_kiosk_check = time.time()

            cv2.imshow("Smart Gate - Camera Feed", frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord(QUIT_KEY):
                cap.release()
                cv2.destroyAllWindows()
                return
                
            if key == ord(CAPTURE_KEY):
                # Use cached status
                if not kiosk_ready:
                    print("\n[BUSY] Complete the current visitor form first!", flush=True)
                    continue

                print("\n[CAPTURE] Starting 3 second countdown...", flush=True)
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
                    
                    # Simple Top-Right Corner UI (Non-obtrusive)
                    display_frame = current_frame.copy()
                    h, w, _ = display_frame.shape
                    
                    # Solid teal box in top right
                    rect_w, rect_h = 80, 80
                    cv2.rectangle(display_frame, (w - rect_w - 20, 20), (w - 20, 20 + rect_h), (136, 148, 13), -1)
                    
                    # Countdown text
                    text = str(remaining)
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    t_size = cv2.getTextSize(text, font, 2, 4)[0]
                    tx = w - 20 - rect_w + (rect_w - t_size[0]) // 2
                    ty = 20 + (rect_h + t_size[1]) // 2
                    cv2.putText(display_frame, text, (tx, ty), font, 2, (255, 255, 255), 4, cv2.LINE_AA)
                    
                    cv2.imshow("Smart Gate - Camera Feed", display_frame)
                    cv2.waitKey(1)

                print("\n[CAPTURE] Image saved. Starting detection...", flush=True)
                os.makedirs("data/captures", exist_ok=True)
                image_path = f"data/captures/detect_{int(time.time())}.jpg"
                cv2.imwrite(image_path, capture_frame)
                
                try:
                    print("[DETECTING] Analyzing plate...", flush=True)
                    plate_number = detect_plate(image_path)
                    
                    if plate_number:
                        print(f"[DETECTED] Plate: {plate_number}", flush=True)
                        result = process_vehicle(plate_number, image_path)
                        
                        if result == "handover":
                            # Release camera so browser can use it for ID scan
                            print("\n[HANDOVER] Releasing camera for Kiosk form...", flush=True)
                            cap.release()
                            cv2.destroyAllWindows()
                            
                            print("[WAITING] Camera paused until form is submitted...", flush=True)
                            while True:
                                if check_kiosk_status():
                                    break
                                time.sleep(2)
                            
                            print("[READY] Form done! Re-acquiring camera...\n", flush=True)
                            time.sleep(1)
                            break  # Break inner loop to re-open camera
                        elif result == "exit":
                            # Exit handled, just continue monitoring
                            continue
                        else:
                            print("[RETRY] Detection failed to process.", flush=True)
                    else:
                        print("[FAILED] No plate detected. Try again.", flush=True)
                except Exception as e:
                    print(f"[CRITICAL ERROR] ANPR failed: {e}", flush=True)

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    run_device_workflow()
