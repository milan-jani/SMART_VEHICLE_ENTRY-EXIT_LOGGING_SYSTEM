"""
Local ANPR Module (YOLOv8 + Enhanced EasyOCR)
Detects license plates using an industry-standard YOLO object detection model.
Extracts text from the upscaled plate using EasyOCR.
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
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

project_root = os.path.join(os.path.dirname(__file__), "..", "..")
models_dir = os.path.join(project_root, "app", "device", "models")
yolo_model_path = os.path.join(models_dir, "license_plate_detector.pt")

plate_detector = None
if YOLO and os.path.exists(yolo_model_path):
    plate_detector = YOLO(yolo_model_path)
    print("[SUCCESS] YOLOv8 Plate Detector Loaded!")
else:
    print(f"[WARNING] YOLO model not ready.")

def validate_and_clean_plate(raw_text: str) -> Optional[str]:
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    # Basic indian format: 2 letters, 2 numbers, 1-2 letters, 4 numbers = ~8-10 chars
    # However, sometimes parts are missing. Let's strictly accept 7 to 11 chars
    if 7 <= len(cleaned) <= 11:
        # NUMBER PLATE MUST START WITH 2 ALPHABETS (e.g. MH, GJ, DL)
        if cleaned[:2].isalpha():
            return cleaned
    return None

def detect_plate_from_image(image_path: str) -> Optional[str]:
    if not plate_detector:
        return None

    print(f"\n[PROCESSING] YOLO Scanning for plates in: {os.path.basename(image_path)}")
    try:
        results = plate_detector(image_path, verbose=False)
        box_data = results[0].boxes
        
        if len(box_data) == 0:
            return None
            
        x1, y1, x2, y2 = map(int, box_data[0].xyxy[0])
        conf = float(box_data[0].conf[0])
        print(f"[SUCCESS-LOCAL] YOLO exactly cropped Plate Region (Confidence: {conf:.2f})")
        
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        plate_crop = img[y1:y2, x1:x2]
        
        # 1. Resize Crop (2x) for EasyOCR (3x might be too large and blur edges)
        plate_crop = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_LANCZOS4)
        
        # 2. Convert to Grayscale
        gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        
        # 3. Apply gentle Contrast Limited Adaptive Histogram Equalization (CLAHE) instead of harsh OTSU threshold
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        contrast_crop = clahe.apply(gray_crop)
        
        print("[PROCESSING] EasyOCR extracting text...")
        ocr_results = reader.readtext(
            contrast_crop, 
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
            paragraph=False
        )
        
        if not ocr_results:
            print("[ERROR] EasyOCR returned NOTHING. Image might be too blurry or dark.")
            return None
            
        # Combine text pieces
        full_text = "".join([piece[1] for piece in ocr_results])
        total_conf = sum([piece[2] for piece in ocr_results])
            
        avg_conf = total_conf / len(ocr_results) if ocr_results else 0
        cleaned_plate = validate_and_clean_plate(full_text)
        
        if cleaned_plate:
            print(f"[SUCCESS-LOCAL] OCR Extracted: {cleaned_plate} (Confidence: {avg_conf:.2f})")
            # If the EasyOCR isn't at least 45% sure, kick it to the Cloud API
            # EasyOCR confidence scores are naturally lower than Cloud API, so 0.45 is a balanced threshold
            if avg_conf < 0.45:
                print(f"[WARNING] Local confidence ({avg_conf:.2f}) is too low, using Cloud API Fallback...")
                return None
            return cleaned_plate
            
        print(f"[ERROR] Found text '{full_text}' but it failed Indian License Plate Regex pattern.")
        return None
        
    except Exception as e:
        print(f"[ERROR] Local pipeline crashed: {str(e)}")
        return None
