"""
Local ANPR Module (YOLOv8 + EasyOCR)
Detects license plates using an industry-standard YOLO object detection model.
Extracts text from the cropped plate using EasyOCR.
"""
import os
import cv2
import easyocr
import re
import warnings
from typing import Optional

# Suppress PyTorch/EasyOCR warnings
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics package not found. Run: pip install ultralytics")
    YOLO = None

print("[INFO] Loading Offline AI Models (YOLOv8 & EasyOCR)...")
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

# Load YOLO model
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
models_dir = os.path.join(project_root, "app", "device", "models")
yolo_model_path = os.path.join(models_dir, "license_plate_detector.pt")

plate_detector = None
if YOLO and os.path.exists(yolo_model_path):
    # ultralytics automatically suppresses some logs when verbose=False in inference
    plate_detector = YOLO(yolo_model_path)
    print("[SUCCESS] YOLOv8 Plate Detector Loaded!")
else:
    print(f"[WARNING] YOLO model not ready (missing file or ultralytics package).")

def validate_and_clean_plate(raw_text: str) -> Optional[str]:
    """
    Cleans up the text by removing non-alphanumeric characters.
    Validates if the text looks roughly like a plate.
    """
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    if 4 <= len(cleaned) <= 12:
        return cleaned
    return None

def detect_plate_from_image(image_path: str) -> Optional[str]:
    """
    Local OCR detection using YOLOv8 for cropping and EasyOCR for reading.
    """
    if not plate_detector:
        print("[ERROR] YOLO model is not initialized. Falling back to API.")
        return None

    print(f"[PROCESSING] YOLO Scanning for plates in: {os.path.basename(image_path)}")
    try:
        # Run YOLO inference
        results = plate_detector(image_path, verbose=False)
        box_data = results[0].boxes
        
        if len(box_data) == 0:
            print("[INFO] YOLO found NO vehicles/plates in the image.")
            return None
            
        # Get coordinates of the best bounding box (highest confidence)
        x1, y1, x2, y2 = map(int, box_data[0].xyxy[0])
        conf = float(box_data[0].conf[0])
        print(f"[SUCCESS-LOCAL] YOLO correctly cropped the Plate Region! (Confidence: {conf:.2f})")
        
        # Crop the plate using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        plate_crop = img[y1:y2, x1:x2]
        
        # EasyOCR prefers grayscale for better text contrast
        gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        
        # EasyOCR text extraction
        ocr_results = reader.readtext(
            gray_crop, 
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )
        
        if not ocr_results:
            print("[ERROR] EasyOCR could not find text inside the YOLO box.")
            return None
            
        # Sort results by Y-coordinate first (top to bottom reading for stacked plates like bikes)
        # However, Indian plates are usually horizontal. If horizontal, sort by X.
        # Let's just combine all text since EasyOCR returns pieces
        full_text = "".join([t[1] for t in ocr_results])
        cleaned_plate = validate_and_clean_plate(full_text)
        
        if cleaned_plate:
            print(f"[SUCCESS-LOCAL] AI Extracted Plate: {cleaned_plate}")
            return cleaned_plate
            
        print("[ERROR] Text found, but did not match a valid license plate format.")
        return None
        
    except Exception as e:
        print(f"[ERROR] Local YOLO+OCR pipeline crashed: {str(e)}")
        return None
