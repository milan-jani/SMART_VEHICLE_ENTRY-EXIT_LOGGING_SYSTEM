import cv2
import os
import sys
import json
from app.api.id_ocr import extract_id_details
from app.device.config import DEFAULT_CAMERA_INDEX

def main():
    print("========================================")
    print("   ID Card OCR - Camera Test Tool")
    print("========================================")
    print("Instructions:")
    print("1. Hold your ID card (DL, Aadhaar, PAN) in front of the camera.")
    print("2. Press 'c' to capture and scan.")
    print("3. Press 'q' to quit.")
    print("========================================\n")

    # Initialize camera
    cap = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    # Ensure data directory exists for temp storage
    os.makedirs("data/temp", exist_ok=True)
    temp_path = "data/temp/id_capture_test.jpg"

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Could not read frame.")
            break

        # Draw a guide frame
        h, w, _ = frame.shape
        cv2.rectangle(frame, (int(w*0.2), int(h*0.2)), (int(w*0.8), int(h*0.8)), (0, 255, 0), 2)
        cv2.putText(frame, "Align ID Card Here", (int(w*0.35), int(h*0.18)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("ID OCR Preview - Press 'c' to Scan", frame)

        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c'):
            print("\n[+] Capturing and scanning...")
            cv2.imwrite(temp_path, frame)
            
            # Call our existing OCR module
            print("[*] Calling Azure OCR API...")
            details = extract_id_details(temp_path, side="front")
            
            if "error" in details:
                print(f"[-] OCR Error: {details['error']}")
            else:
                print("\n" + "="*30)
                print("   EXTRACTED DETAILS")
                print("="*30)
                print(f"Name:        {details.get('name', '-')}")
                print(f"ID Number:   {details.get('id_number', '-')}")
                print(f"Date of Birth: {details.get('dob', '-')}")
                print(f"Confidence:  {details.get('confidence', 0)*100:.1f}%")
                print("="*30)
                
            print("\n[!] Ready for next capture. Press 'c' to scan again or 'q' to quit.")

    cap.release()
    cv2.destroyAllWindows()
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)

if __name__ == "__main__":
    main()
