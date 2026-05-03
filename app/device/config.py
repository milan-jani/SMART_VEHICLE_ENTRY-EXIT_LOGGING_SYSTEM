"""
Configuration
Device and API configuration settings
"""
import os
from dotenv import load_dotenv

# Load .env file if it exists, otherwise check .env.example
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists(".env.example"):
    load_dotenv(".env.example")

# Camera Configuration
DEFAULT_CAMERA_INDEX = 0 # Change this: 0 = laptop camera, 1 = external camera, etc.
CAPTURE_KEY = 'c'  # Key to press for capture
QUIT_KEY = 'q'     # Key to press to quit

# ANPR API Configuration
ANPR_MODE = "hybrid"  # options: 'local', 'api', 'hybrid'
PLATE_RECOGNIZER_API_KEY = os.getenv("PLATE_RECOGNIZER_API_KEY", "")
PLATE_RECOGNIZER_ENDPOINT = "https://api.platerecognizer.com/v1/plate-reader/"

# Azure Computer Vision API Configuration (Phase 6)
AZURE_CV_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT", "")
AZURE_CV_KEY = os.getenv("AZURE_CV_KEY", "")

# Backend API Configuration
# Change this to your deployed backend URL when in production
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_NEW_ENTRY = f"{API_BASE_URL}/api/new-entry"
API_UPDATE_EXIT = f"{API_BASE_URL}/api/update-exit"
API_UPDATE_DETAILS = f"{API_BASE_URL}/api/update-details"
API_GET_VEHICLES = f"{API_BASE_URL}/api/vehicles"
API_FORM_URL = f"{API_BASE_URL}/api/form"
API_KIOSK_URL = f"{API_BASE_URL}/api/kiosk"  # Phase 5: Kiosk UI

# File Paths
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
PHOTOS_DIR = os.path.join(DATA_DIR, "photos")

# Ensure directories exist
os.makedirs(PHOTOS_DIR, exist_ok=True)

# Device Behavior
AUTO_OPEN_FORM = True      # Automatically open form after new entry
FORM_TIMEOUT = 300         # Seconds to wait for form submission (5 minutes)
CONTINUOUS_MODE = True     # Keep camera running continuously (True = real-world mode)

# Logging
ENABLE_DEBUG_LOGS = True
