import requests
import time
from typing import Optional, Dict

try:
    from .config import ANPR_KEYS, PLATE_RECOGNIZER_ENDPOINT
except (ImportError, ValueError):
    from config import ANPR_KEYS, PLATE_RECOGNIZER_ENDPOINT

def detect_plate(image_path: str) -> Optional[str]:
    """
    Detect license plate number from an image using PlateRecognizer API.
    Rotates through multiple keys if one fails or hits rate limits.
    """
    print(f"[DEBUG] Reading image file: {image_path}")
    
    for i, key in enumerate(ANPR_KEYS):
        if not key:
            continue
            
        print(f"[DEBUG] Trying key {i+1} (...{key[-6:]})")
        try:
            with open(image_path, 'rb') as img_file:
                response = requests.post(
                    PLATE_RECOGNIZER_ENDPOINT,
                    files=dict(upload=img_file),
                    headers={'Authorization': f'Token {key}'},
                    timeout=15
                )
            
            # Check for success
            if response.status_code in (200, 201):
                result = response.json()
                if result.get("results") and len(result["results"]) > 0:
                    plate_number = result["results"][0]["plate"].upper()
                    confidence = result["results"][0].get("score", 0)
                    print(f"[SUCCESS] Detected: {plate_number} (Score: {confidence:.2f})")
                    return plate_number
                else:
                    print(f"[WARNING] No plate found with key {i+1}.")
                    return None # If it read but found nothing, no point in rotating
            
            # If rate limited (429) or other error, try next key
            elif response.status_code == 429:
                print(f"[RATE LIMIT] Key {i+1} is busy. Trying next key...")
                continue
            else:
                print(f"[ERROR] API Key {i+1} error {response.status_code}: {response.text}")
                continue
        
        except Exception as e:
            print(f"[ERROR] Key {i+1} failed: {str(e)}")
            continue
            
    print("[FATAL] All ANPR keys failed or no plate found.")
    return None
