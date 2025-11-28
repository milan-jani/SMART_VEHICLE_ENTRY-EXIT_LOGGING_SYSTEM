"""
Configuration
Device and API configuration settings
"""
import os

# Camera Configuration
DEFAULT_CAMERA_INDEX = 0
CAPTURE_KEY = 'c'  # Key to press for capture
QUIT_KEY = 'q'     # Key to press to quit

# ANPR API Configuration
PLATE_RECOGNIZER_API_KEY = "be5b13c29a83097837f0a4983efc62a5e1bb6d98"
PLATE_RECOGNIZER_ENDPOINT = "https://api.platerecognizer.com/v1/plate-reader/"

# Backend API Configuration
# Change this to your deployed backend URL when in production
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_NEW_ENTRY = f"{API_BASE_URL}/api/new-entry"
API_UPDATE_EXIT = f"{API_BASE_URL}/api/update-exit"
API_UPDATE_DETAILS = f"{API_BASE_URL}/api/update-details"
API_GET_VEHICLES = f"{API_BASE_URL}/api/vehicles"
API_FORM_URL = f"{API_BASE_URL}/api/form"

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
