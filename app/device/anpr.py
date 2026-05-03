import requests
from typing import Optional, Dict

# Cloud API Configuration (PlateRecognizer)
API_KEY = "be5b13c29a83097837f0a4983efc62a5e1bb6d98"
API_ENDPOINT = "https://api.platerecognizer.com/v1/plate-reader/"

def detect_plate(image_path: str) -> Optional[str]:
    """
    Detect license plate number from an image using PlateRecognizer API
    """
    print(f"[DEBUG] Reading image file: {image_path}")
    try:
        with open(image_path, 'rb') as img_file:
            print("[DEBUG] Sending request to PlateRecognizer...")
            response = requests.post(
                API_ENDPOINT,
                files=dict(upload=img_file),
                headers={'Authorization': f'Token {API_KEY}'},
                timeout=15
            )
        
        # Check if request was successful
        if response.status_code != 201 and response.status_code != 200:
            print(f"[ERROR] API returned error {response.status_code}: {response.text}")
            return None

        result = response.json()
        print(f"[DEBUG] API Response: {result}")
        
        if result.get("results") and len(result["results"]) > 0:
            plate_number = result["results"][0]["plate"].upper()
            confidence = result["results"][0].get("score", 0)
            print(f"[SUCCESS] Detected: {plate_number} (Score: {confidence:.2f})")
            return plate_number
        else:
            print("[WARNING] No plate found in this image.")
            return None
    
    except Exception as e:
        print(f"[CRITICAL ERROR] anpr.py failure: {str(e)}")
        return None
