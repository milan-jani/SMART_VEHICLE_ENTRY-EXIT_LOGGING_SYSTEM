"""
Device Runner
Main workflow for device operation: capture, detect, and communicate with API
"""
import requests
import webbrowser
from datetime import datetime
from typing import Optional

from app.device.camera import capture_with_preview
from app.device.anpr import detect_plate_from_image
from app.device.config import (
    DEFAULT_CAMERA_INDEX,
    API_NEW_ENTRY,
    API_UPDATE_EXIT,
    API_FORM_URL,
    AUTO_OPEN_FORM
)


def send_new_entry(vehicle_no: str, image_path: str) -> dict:
    """
    Send new entry to backend API
    
    Args:
        vehicle_no: Detected vehicle number
        image_path: Path to captured image
    
    Returns:
        Dictionary with 'success' (bool) and 'status' (str: 'new' or 'existing')
    """
    try:
        in_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "vehicle_no": vehicle_no,
            "image_path": image_path,
            "in_time": in_time
        }
        
        response = requests.post(API_NEW_ENTRY, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            api_status = result.get('status', 'success')
            
            if api_status == 'warning':
                # Vehicle already has an open entry (already inside)
                print(f"⚠️ {result.get('message', 'Vehicle already inside')}")
                return {'success': True, 'status': 'existing'}
            else:
                # New entry created successfully
                print(f"✅ {result.get('message', 'Entry created successfully')}")
                return {'success': True, 'status': 'new'}
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return {'success': False, 'status': 'error'}
    
    except requests.RequestException as e:
        print(f"❌ Failed to send entry to API: {str(e)}")
        print("⚠️ Make sure the backend server is running!")
        return {'success': False, 'status': 'error'}


def send_exit_update(vehicle_no: str) -> bool:
    """
    Send exit time update to backend API
    
    Args:
        vehicle_no: Vehicle number
    
    Returns:
        True if successful, False otherwise
    """
    try:
        out_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        payload = {
            "vehicle_no": vehicle_no,
            "out_time": out_time
        }
        
        response = requests.post(API_UPDATE_EXIT, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result.get('message', 'Exit updated successfully')}")
            return True
        elif response.status_code == 404:
            print(f"⚠️ No open entry found for vehicle {vehicle_no}")
            return False
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
    
    except requests.RequestException as e:
        print(f"❌ Failed to send exit update to API: {str(e)}")
        print("⚠️ Make sure the backend server is running!")
        return False


def check_existing_entry(vehicle_no: str) -> Optional[dict]:
    """
    Check if vehicle has an existing open entry
    
    Args:
        vehicle_no: Vehicle number to check
    
    Returns:
        Existing entry data if found, None otherwise
    """
    try:
        # This would require a new API endpoint to check vehicle status
        # For now, we'll handle this in send_new_entry response
        pass
    except Exception as e:
        print(f"❌ Error checking existing entry: {str(e)}")
    return None


def open_visitor_form(vehicle_no: str) -> None:
    """
    Open visitor form in browser
    
    Args:
        vehicle_no: Vehicle number to pre-fill in form
    """
    try:
        form_url = f"{API_FORM_URL}?plate={vehicle_no}"
        print(f"🌐 Opening visitor form: {form_url}")
        webbrowser.open(form_url)
    except Exception as e:
        print(f"❌ Failed to open form: {str(e)}")


def process_vehicle(plate_number: str, image_path: str) -> None:
    """
    Process a detected vehicle (check status and update)
    
    Args:
        plate_number: Detected plate number
        image_path: Path to captured image
    """
    print(f"\n✅ Plate detected: {plate_number}")
    
    # Check vehicle status and send to API
    print("📤 Checking vehicle status...")
    entry_result = send_new_entry(plate_number, image_path)
    
    if not entry_result['success']:
        # API error - could not process
        print("⚠️ Could not process vehicle. Check API logs.")
    
    elif entry_result['status'] == 'new':
        # New vehicle entry created - open form for visitor details
        print(f"🆕 New vehicle entry created!")
        print(f"📋 Vehicle {plate_number} marked as INSIDE")
        
        if AUTO_OPEN_FORM:
            print("🌐 Opening visitor form...")
            open_visitor_form(plate_number)
            print("⏳ Please fill out the visitor form in your browser.")
        else:
            print(f"💡 Visit {API_FORM_URL}?plate={plate_number} to fill visitor details")
    
    elif entry_result['status'] == 'existing':
        # Vehicle already has an open entry (already inside) - mark as exit
        print(f"🔄 Vehicle {plate_number} is already INSIDE")
        print("📤 Marking as EXIT...")
        
        exit_success = send_exit_update(plate_number)
        
        if exit_success:
            print(f"✅ Vehicle {plate_number} marked as EXITED!")
            print(f"🚗 Exit time recorded successfully")
        else:
            print(f"❌ Failed to record exit time")


def run_device_workflow(camera_index: int = DEFAULT_CAMERA_INDEX) -> None:
    """
    Main device workflow - Continuous monitoring mode
    Keeps camera running and processes vehicles as they arrive
    
    1. Camera stays ON continuously
    2. Press 'c' to capture and process vehicle
    3. Press 'q' to quit and close camera
    
    Args:
        camera_index: Camera device index
    """
    print("\n" + "="*60)
    print("🚗 HYBRID LOGGING SYSTEM - CONTINUOUS MONITORING MODE")
    print("="*60 + "\n")
    print("📹 Camera will stay ON continuously")
    print("📸 Press 'c' to capture and process vehicle")
    print("❌ Press 'q' to quit and close camera")
    print("\n" + "="*60 + "\n")
    
    import cv2
    import time
    import os
    
    # Open camera once
    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("❌ Camera not found. Please check camera connection.")
        return
    
    print("✅ Camera initialized successfully!")
    print("🎥 Live preview starting...\n")
    
    try:
        while True:
            # Read frame from camera
            ret, frame = cap.read()
            if not ret:
                print("⚠️ Failed to capture frame. Retrying...")
                continue
            
            # Show live preview
            cv2.imshow("🚗 Hybrid Logging System - Press 'c' to capture | 'q' to quit", frame)
            
            # Wait for key press (1ms delay)
            key = cv2.waitKey(1) & 0xFF
            
            if key == ord('c'):
                # Capture button pressed
                print("\n" + "-"*60)
                print("📸 Capturing image...")
                
                # Save image to photos directory
                photo_dir = os.path.join(
                    os.path.dirname(__file__),
                    "..", "..",
                    "data", "photos"
                )
                os.makedirs(photo_dir, exist_ok=True)
                image_path = os.path.join(photo_dir, f"capture_{int(time.time())}.jpg")
                
                cv2.imwrite(image_path, frame)
                print(f"🖼️ Saved: {image_path}")
                
                # Detect plate number
                print("🔍 Detecting plate number...")
                plate_number = detect_plate_from_image(image_path)
                
                if not plate_number:
                    print("❌ No plate detected. Please try again.")
                    print("-"*60 + "\n")
                    print("🎥 Camera still running... Press 'c' to capture again")
                    continue
                
                # Process the vehicle
                process_vehicle(plate_number, image_path)
                
                print("-"*60 + "\n")
                print("🎥 Camera still running... Ready for next vehicle")
                print("📸 Press 'c' to capture | 'q' to quit\n")
            
            elif key == ord('q'):
                # Quit button pressed
                print("\n" + "="*60)
                print("🛑 Shutting down camera...")
                break
    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user (Ctrl+C)")
    
    finally:
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        print("✅ Camera closed successfully")
        print("="*60 + "\n")


def main():
    """
    Entry point for device runner
    """
    try:
        run_device_workflow()
    except KeyboardInterrupt:
        print("\n\n⚠️ Workflow interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
