"""
ANPR Module
Handles Automatic Number Plate Recognition using PlateRecognizer API
"""
import requests
from typing import Optional, Dict

# API Configuration
API_KEY = "be5b13c29a83097837f0a4983efc62a5e1bb6d98"
API_ENDPOINT = "https://api.platerecognizer.com/v1/plate-reader/"


def detect_plate_from_image(image_path: str) -> Optional[str]:
    """
    Detect license plate number from an image using PlateRecognizer API
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Detected plate number (uppercase) or None if not detected
    """
    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                API_ENDPOINT,
                files=dict(upload=img_file),
                headers={'Authorization': f'Token {API_KEY}'}
            )
        
        result = response.json()
        
        if result.get("results") and len(result["results"]) > 0:
            plate_number = result["results"][0]["plate"].upper()
            confidence = result["results"][0].get("score", 0)
            print(f"[DETECTED] Plate: {plate_number} (Confidence: {confidence:.2f})")
            return plate_number
        else:
            print("[ERROR] No plate detected in image.")
            return None
    
    except FileNotFoundError:
        print(f"[ERROR] Image file not found: {image_path}")
        return None
    except requests.RequestException as e:
        print(f"[ERROR] API request failed: {str(e)}")
        return None
    except Exception as e:
        print(f"[ERROR] Error detecting plate: {str(e)}")
        return None


def detect_plate_with_details(image_path: str) -> Optional[Dict]:
    """
    Detect license plate with detailed information
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Dictionary with plate details or None if not detected
    """
    try:
        with open(image_path, 'rb') as img_file:
            response = requests.post(
                API_ENDPOINT,
                files=dict(upload=img_file),
                headers={'Authorization': f'Token {API_KEY}'}
            )
        
        result = response.json()
        
        if result.get("results") and len(result["results"]) > 0:
            plate_data = result["results"][0]
            return {
                "plate": plate_data["plate"].upper(),
                "confidence": plate_data.get("score", 0),
                "region": plate_data.get("region", {}).get("code", "Unknown"),
                "vehicle_type": plate_data.get("vehicle", {}).get("type", "Unknown"),
                "box": plate_data.get("box", {})
            }
        else:
            print("[ERROR] No plate detected in image.")
            return None
    
    except Exception as e:
        print(f"[ERROR] Error detecting plate: {str(e)}")
        return None


def validate_plate_format(plate: str) -> bool:
    """
    Basic validation for plate number format
    
    Args:
        plate: Plate number string
    
    Returns:
        True if valid format, False otherwise
    """
    if not plate or len(plate) < 3:
        return False
    
    # Remove spaces and check if alphanumeric
    cleaned = plate.replace(" ", "").replace("-", "")
    return cleaned.isalnum() and len(cleaned) >= 3
