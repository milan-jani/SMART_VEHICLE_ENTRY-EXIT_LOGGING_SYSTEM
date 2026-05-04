"""
Local ANPR Module (YOLOv8 + EasyOCR)
Uses the trained YOLOv8 model from codewithaarohi/ANPR repo (best.pt)
Same approach: YOLO detect plate -> crop -> EasyOCR read text
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
    print("[ERROR] ultralytics package not found.")
    YOLO = None

print("[INFO] Loading Offline AI Models (YOLOv8 & EasyOCR)...")
# Create a local directory for models to avoid permission/network checks
local_model_dir = os.path.join(os.path.dirname(__file__), "models", "easyocr")
os.makedirs(local_model_dir, exist_ok=True)

reader = easyocr.Reader(['en'], gpu=False, verbose=False, model_storage_directory=local_model_dir, download_enabled=True)

project_root = os.path.join(os.path.dirname(__file__), "..", "..")
models_dir = os.path.join(project_root, "app", "device", "models")
yolo_model_path = os.path.join(models_dir, "license_plate_detector.pt")

plate_detector = None
if YOLO and os.path.exists(yolo_model_path):
    plate_detector = YOLO(yolo_model_path)
    print("[SUCCESS] YOLOv8 Plate Detector Loaded!")
    # Warm up YOLO model with a dummy blank image to speed up first detection
    try:
        import numpy as np
        dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
        plate_detector(dummy_img, verbose=False)
        print("[INFO] YOLO Model warmed up and ready.")
    except Exception:
        pass
else:
    print(f"[WARNING] YOLO model not ready.")


# Common OCR confusions between letters and numbers
NUM_TO_LETTER = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
LETTER_TO_NUM = {'O': '0', 'I': '1', 'Z': '2', 'S': '5', 'B': '8', 'D': '0', 'Q': '0', 'G': '6'}


def validate_and_clean_plate(raw_text: str) -> Optional[str]:
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    # Basic cleanup: if starts with number that looks like letter, fix it
    if len(cleaned) > 2 and cleaned[0].isdigit():
        mapping = {'0': 'O', '1': 'I', '2': 'Z', '5': 'S', '8': 'B'}
        if cleaned[0] in mapping:
            cleaned = mapping[cleaned[0]] + cleaned[1:]
            
    if 7 <= len(cleaned) <= 11:
        if cleaned[:2].isalpha():
            return cleaned
    return None

def perform_ocr_on_image(img, coordinates):
    """Same OCR approach but returning confidence to trigger fallback if needed"""
    x, y, w, h = map(int, coordinates)
    cropped_img = img[y:h, x:w]
    
    # 1. Resize Crop (2x) for EasyOCR
    cropped_img = cv2.resize(cropped_img, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
    # 2. Convert to Grayscale
    gray_img = cv2.cvtColor(cropped_img, cv2.COLOR_BGR2GRAY)
    # 3. Apply CLAHE contrast
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    contrast_img = clahe.apply(gray_img)

    results = reader.readtext(contrast_img)
    
    text = ""
    conf = 0.0
    for res in results:
        if len(results) == 1 or (len(res[1]) > 6 and res[2] > 0.2):
            text = res[1]
            conf = res[2]
            
    return str(text), conf

def detect_plate_from_image(image_path: str) -> Optional[str]:
    if not plate_detector:
        return None

    print(f"\n[PROCESSING] YOLO Scanning for plates in: {os.path.basename(image_path)}")
    try:
        results = plate_detector(image_path, verbose=False)
        box_data = results[0].boxes
        
        if len(box_data) == 0:
            return None
        
        # Get best detection
        x1, y1, x2, y2 = map(int, box_data[0].xyxy[0])
        conf = float(box_data[0].conf[0])
        print(f"[SUCCESS-LOCAL] YOLO Plate Detected (Confidence: {conf:.2f})")
        
        img = cv2.imread(image_path)
        if img is None:
            return None
        
        text_ocr, ocr_conf = perform_ocr_on_image(img, [x1, y1, x2, y2])
        
        if text_ocr:
            cleaned_plate = validate_and_clean_plate(text_ocr)
            if cleaned_plate:
                print(f"[SUCCESS-LOCAL] OCR Extracted: {cleaned_plate} (Confidence: {ocr_conf:.2f})")
                # Fallback to Cloud API if confidence is too low (User requested 80-85%)
                if ocr_conf < 0.85:
                    print(f"[WARNING] Local confidence ({ocr_conf:.2f}) is below 85%. Sending to Cloud API fallback...")
                    return None
                return cleaned_plate
            else:
                print(f"[ERROR] Found text '{text_ocr}' but failed Indian plate format check.")
                return None
        
        print("[ERROR] EasyOCR returned NOTHING.")
        return None
        
    except Exception as e:
        print(f"[ERROR] Local pipeline crashed: {str(e)}")
        return None
