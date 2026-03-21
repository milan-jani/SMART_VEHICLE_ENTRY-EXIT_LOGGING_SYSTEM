"""
Local ANPR Module (Offline Optical Character Recognition)
Handles Number Plate Recognition using local device CPU/GPU and EasyOCR.
Does NOT require an active internet connection or paid API credits.
"""
import os
import cv2
import easyocr
import numpy as np
import re
import warnings
from typing import Optional, Dict

# Suppress warnings from PyTorch/EasyOCR to keep the console clean
warnings.filterwarnings("ignore", category=UserWarning)

print("[INFO] Loading Offline AI OCR Model... (This might take a few seconds on first run)")
# Initialize the reader globally so it doesn't load into memory on every request
# gpu=False ensures it runs everywhere (like Raspberry Pi). Toggle to True if you have a CUDA/Nvidia card.
reader = easyocr.Reader(['en'], gpu=False, verbose=False)

def preprocess_image(image_path: str):
    """
    Advanced preprocessing: Finds the license plate contour and crops it out.
    If no contour is found, it falls back to the full grayscale image.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) # Noise reduction
    edged = cv2.Canny(bfilter, 30, 200) # Edge detection
    
    # Find contours
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10] # Top 10 biggest shapes
    
    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4: # finding a rectangular shape roughly
            location = approx
            break
            
    if location is None:
        print("[INFO] No clear plate contour found, scanning full image...")
        return bfilter # Fallback to original blurred image
        
    # Create mask and crop
    mask = np.zeros(gray.shape, np.uint8)
    cv2.drawContours(mask, [location], 0, 255, -1)
    
    try:
        (x, y) = np.where(mask == 255)
        (x1, y1) = (np.min(x), np.min(y))
        (x2, y2) = (np.max(x), np.max(y))
        cropped_image = gray[x1:x2+1, y1:y2+1]
        print("[INFO] Plate cleanly cropped from background!")
        return cropped_image
    except Exception:
        print("[INFO] Error cropping Plate, scanning full image...")
        return bfilter

def validate_and_clean_plate(raw_text: str) -> Optional[str]:
    """
    Cleans up the text by removing non-alphanumeric characters.
    Validates if the text looks roughly like a plate.
    """
    # Remove everything except standard English letters and Numbers
    cleaned = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    
    # Common OCR mixups substitution
    replacements = {
        'O': '0',
        'I': '1',
    }
    
    # Note: We won't blindly swap letters for numbers unless we verify the slot, 
    # so we just keep the cleaned string for now as EasyOCR is fairly accurate.
    
    # Indian plates are usually 9-10 chars (e.g., MH20EJ0364)
    # But sometimes state code falls off. We'll accept anything between 4 and 10 characters.
    if len(cleaned) >= 4 and len(cleaned) <= 12:
        return cleaned
    return None

def detect_plate_from_image(image_path: str) -> Optional[str]:
    """
    Local OCR detection pipeline using EasyOCR.
    
    Args:
        image_path: Path to the vehicle image
        
    Returns:
        Detected plate number (uppercase and clean) or None
    """
    print(f"[PROCESSING] Running offline OCR on: {os.path.basename(image_path)}")
    try:
        processed_img = preprocess_image(image_path)
        if processed_img is None:
            print(f"[ERROR] Could not read image at path: {image_path}")
            return None
            
        # Extract text from the processed image
        # allowlist limits prediction to valid Indian plate characters
        results = reader.readtext(
            processed_img, 
            allowlist='0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        )
        
        if not results:
            print("[ERROR] AI could not find any text in the image.")
            return None
            
        # Results format: [(bounding_box, 'text', confidence_score), ...]
        # Sort results by confidence score (Highest confidence first)
        sorted_results = sorted(results, key=lambda x: x[2], reverse=True)
        
        for bbox, text, prob in sorted_results:
            cleaned_plate = validate_and_clean_plate(text)
            if cleaned_plate:
                print(f"[SUCCESS-LOCAL] AI extracted Plate: {cleaned_plate} (Confidence: {prob:.2f})")
                return cleaned_plate
                
        print("[ERROR] Text found, but did not match any valid license plate format.")
        return None
        
    except Exception as e:
        print(f"[ERROR] Local OCR pipeline crashed: {str(e)}")
        return None
