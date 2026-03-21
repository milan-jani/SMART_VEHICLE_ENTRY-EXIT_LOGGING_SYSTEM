"""
Local ANPR Module (Offline Optical Character Recognition)
Handles Number Plate Recognition using local device CPU/GPU and EasyOCR.
Does NOT require an active internet connection or paid API credits.
"""
import os
import cv2
import easyocr
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
    Applies filters to the image to make it easier for OCR to read the text.
    Converts to grayscale and reduces noise.
    """
    img = cv2.imread(image_path)
    if img is None:
        return None
        
    # Convert to grayscale (OCR loves high contrast B&W)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Noise reduction (Bilateral filter keeps edges sharp but blurs the rest)
    bfilter = cv2.bilateralFilter(gray, 11, 17, 17) 
    
    # Additional edge detection or thresholding could be added here if needed,
    # but EasyOCR works quite well with just clean grayscale.
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
