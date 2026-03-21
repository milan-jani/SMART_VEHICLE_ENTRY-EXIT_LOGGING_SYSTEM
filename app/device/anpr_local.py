"""
Local ANPR Module (YOLOv8 + PaddleOCR)
Detects license plates using an industry-standard YOLO object detection model.
Extracts text from the cropped plate using Baidu's highly accurate PaddleOCR.
"""
import os
import cv2
import re
import warnings
from typing import Optional

# Suppress warnings
warnings.filterwarnings("ignore", category=UserWarning)

try:
    from ultralytics import YOLO
except ImportError:
    print("[ERROR] ultralytics package not found. Run: pip install ultralytics")
    YOLO = None

import logging
logging.getLogger("ppocr").setLevel(logging.WARNING) # Suppress PaddleOCR spam

try:
    from paddleocr import PaddleOCR
    # Initialize PaddleOCR globally (loads once). lang='en' for English alphabets and numbers
    # show_log=False prevents excessive terminal spam, use_angle_cls=True handles slight tilts
    ocr_reader = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
except ImportError:
    print("[ERROR] paddleocr package not found. Run: pip install paddlepaddle paddleocr")
    ocr_reader = None

print("[INFO] Loading Offline AI Models (YOLOv8 & PaddleOCR)...")

# Load YOLO model
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
models_dir = os.path.join(project_root, "app", "device", "models")
yolo_model_path = os.path.join(models_dir, "license_plate_detector.pt")

plate_detector = None
if YOLO and os.path.exists(yolo_model_path):
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
    # Indian plates are typically 8-10 chars. Let's accept 4 to 12 just in case.
    if 4 <= len(cleaned) <= 12:
        return cleaned
    return None

def detect_plate_from_image(image_path: str) -> Optional[str]:
    """
    Local OCR detection using YOLOv8 for cropping and PaddleOCR for reading.
    Returns cleaned plate ONLY if PaddleOCR confidence is high enough.
    """
    if not plate_detector or not ocr_reader:
        print("[ERROR] AI models are not initialized. Falling back to API.")
        return None

    print(f"\n[PROCESSING] YOLO Scanning for plates in: {os.path.basename(image_path)}")
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
        print(f"[SUCCESS-LOCAL] YOLO exactly cropped the Plate Region! (Confidence: {conf:.2f})")
        
        # Crop the plate using OpenCV
        img = cv2.imread(image_path)
        if img is None:
            return None
            
        plate_crop = img[y1:y2, x1:x2]
        
        # Super-Resolution & Pre-processing for OCR
        # 1. Resize Crop (2x) to make characters larger for PaddleOCR
        plate_crop = cv2.resize(plate_crop, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        # 2. Convert to Grayscale
        gray_crop = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        
        print("[PROCESSING] PaddleOCR reading text...")
        # PaddleOCR extraction
        ocr_results = ocr_reader.ocr(gray_crop, cls=True)
        
        if not ocr_results or not ocr_results[0]:
            print("[ERROR] PaddleOCR could not find text inside the YOLO box.")
            return None
            
        # ocr_results[0] is a list of lines: [[[x,y coords], ('text', confidence)], ...]
        full_text = ""
        total_conf = 0.0
        piece_count = 0
        
        for line in ocr_results[0]:
            text, text_conf = line[1]
            full_text += text
            total_conf += text_conf
            piece_count += 1
            
        avg_conf = total_conf / piece_count if piece_count > 0 else 0
        cleaned_plate = validate_and_clean_plate(full_text)
        
        if cleaned_plate:
            print(f"[SUCCESS-LOCAL] PaddleOCR Extracted: {cleaned_plate} (Confidence: {avg_conf:.2f})")
            
            # STRICT CONFIDENCE CHECK (0.85 = 85%)
            if avg_conf < 0.85:
                print(f"[WARNING] Local OCR confidence ({avg_conf:.2f}) is below 85% threshold. Falling back to Cloud API...")
                return None
                
            return cleaned_plate
            
        print("[ERROR] Text found, but did not match a valid license plate format.")
        return None
        
    except Exception as e:
        print(f"[ERROR] Local YOLO+PaddleOCR pipeline crashed: {str(e)}")
        return None
