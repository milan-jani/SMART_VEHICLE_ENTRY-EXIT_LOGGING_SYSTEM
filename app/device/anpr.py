import requests
import os
from typing import Optional
from dotenv import load_dotenv

# Load env
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists(".env.example"):
    load_dotenv(".env.example")

# Both keys from env — KEY_1 is expired, so try KEY_2 first
API_KEY_1 = os.getenv("PLATE_RECOGNIZER_API_KEY_1", "")
API_KEY_2 = os.getenv("PLATE_RECOGNIZER_API_KEY_2", "")
API_ENDPOINT = "https://api.platerecognizer.com/v1/plate-reader/"

def _try_detect(image_path: str, api_key: str) -> Optional[dict]:
    """Try detection with a specific API key. Returns response dict or None."""
    with open(image_path, 'rb') as img_file:
        response = requests.post(
            API_ENDPOINT,
            files=dict(upload=img_file),
            headers={'Authorization': f'Token {api_key}'},
            timeout=15
        )
    if response.status_code in (200, 201):
        return response.json()
    print(f"[WARN] API key ending ...{api_key[-6:]} returned {response.status_code}")
    return None

def detect_plate(image_path: str) -> Optional[str]:
    """
    Detect license plate from image.
    Tries KEY_2 first (KEY_1 is expired), falls back to KEY_1.
    """
    print(f"[DEBUG] Reading image file: {image_path}")
    
    keys_to_try = [k for k in [API_KEY_2, API_KEY_1] if k]
    
    if not keys_to_try:
        print("[ERROR] No PLATE_RECOGNIZER_API_KEY set in .env or .env.example!")
        return None

    for key in keys_to_try:
        try:
            print(f"[DEBUG] Trying key ...{key[-6:]}")
            result = _try_detect(image_path, key)
            if result and result.get("results"):
                plate = result["results"][0]["plate"].upper()
                score = result["results"][0].get("score", 0)
                print(f"[SUCCESS] Detected: {plate} (Score: {score:.2f})")
                return plate
            elif result:
                print("[WARNING] No plate found in this image.")
                return None
        except Exception as e:
            print(f"[WARN] Key ...{key[-6:]} failed: {e}")
            continue

    print("[ERROR] All API keys failed.")
    return None
