import os
import time
import cv2
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables (try .env first, then .env.example)
if os.path.exists(".env"):
    load_dotenv(".env")
elif os.path.exists(".env.example"):
    print("[!] Warning: Using values from .env.example. Recommended: create a .env file.")
    load_dotenv(".env.example")
else:
    print("[!] Warning: No .env or .env.example found. Environment variables must be set manually.")

from app.api.id_ocr import extract_id_details
from app.device.config import AZURE_CV_ENDPOINT, AZURE_CV_KEY


BLUR_THRESHOLD = 80.0


def calc_blur_score(frame):
    """
    Calculate sharpness/blur score using Laplacian variance.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def _get_raw_lines(image_path):
    """
    Extracts raw text lines from image via Azure OCR.
    Returns the list of raw text lines, or None if error.
    """
    import requests as req

    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        return None

    full_path = os.path.abspath(image_path)
    if not os.path.exists(full_path):
        return None

    analyze_url = f"{AZURE_CV_ENDPOINT.rstrip('/')}/vision/v3.2/read/analyze"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_CV_KEY,
        'Content-Type': 'application/octet-stream'
    }

    try:
        with open(full_path, "rb") as f:
            resp = req.post(analyze_url, headers=headers, data=f)

        if resp.status_code not in [200, 202]:
            return None

        op_url = resp.headers.get("Operation-Location")
        if not op_url:
            return None

        poll_headers = {'Ocp-Apim-Subscription-Key': AZURE_CV_KEY}
        for _ in range(15):
            time.sleep(1.0)
            poll_resp = req.get(op_url, headers=poll_headers)
            result = poll_resp.json()
            if result.get("status") == "succeeded":
                lines = []
                for page in result.get("analyzeResult", {}).get("readResults", []):
                    for line in page.get("lines", []):
                        lines.append(line.get("text", "").strip())
                return lines
            elif result.get("status") == "failed":
                return None
    except Exception:
        return None

    return None


def show_all_results(front_data, back_data, raw_lines, image_path, blur_score):
    """Display results in a formatted output (console)."""
    print()
    print("╔════════════════════════════════════════════════════════╗")
    print("║           📋  SCAN RESULTS  (Image Mode)  📋           ║")
    print("╚════════════════════════════════════════════════════════╝")

    quality = "Excellent" if blur_score > 200 else "Good" if blur_score > BLUR_THRESHOLD else "Fair (may affect accuracy)"
    quality_icon = "🟢" if blur_score > 200 else "🟡" if blur_score > BLUR_THRESHOLD else "🔴"
    print(f"\n{quality_icon}  Image Quality: {quality} (sharpness: {blur_score:.0f})")

    if front_data:
        if "error" in front_data:
            print("\n⚠️  FRONT SIDE — Error:\n   ", front_data['error'])
        else:
            print("\n🪪  PERSONAL DETAILS (Front Side)")
            print(f"  👤 Name      : {front_data.get('name','— (not detected)')}")
            print(f"  🔢 ID Number : {front_data.get('id_number','— (not detected)')}")
            print(f"  📅 DOB       : {front_data.get('dob','— (not detected)')}")
            conf = front_data.get('confidence', 0)
            print(f"  📊 Confidence: {conf*100:.0f}%")

    if back_data:
        if "error" in back_data:
            print("\n⚠️  BACK SIDE — Error:\n   ", back_data['error'])
        else:
            has_address = any([
                back_data.get('address_street'),
                back_data.get('address_city'),
                back_data.get('address_state')
            ])
            if has_address:
                print("\n🏠  ADDRESS DETAILS (Back Side)")
                print(f"  📍 Street : {back_data.get('address_street','— (not detected)')}")
                print(f"  🏙️ City   : {back_data.get('address_city','— (not detected)')}")
                print(f"  🗺️ State  : {back_data.get('address_state','— (not detected)')}")
                conf = back_data.get('confidence', 0)
                print(f"  📊 Confidence: {conf*100:.0f}%")

    if raw_lines:
        print("\n📝  RAW OCR TEXT (all lines detected):")
        for i, line in enumerate(raw_lines, 1):
            print(f"  {i:2d}. {line}")

    print()
    print(f"💾  Image path: {os.path.abspath(image_path)}")
    print()


def main():
    import sys

    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
    else:
        image_path = input("Enter path to existing image file: ").strip('"')

    if not os.path.exists(image_path):
        print("Error: file not found:", image_path)
        return

    # Compute blur score for the image (optional quality metric)
    frame = cv2.imread(image_path)
    if frame is None:
        print("Error: OpenCV could not read the image. Check file format.")
        return

    blur_score = calc_blur_score(frame)

    print("\n⏳  Sending image to OCR (Azure) — extracting front and back details...")
    front_data = extract_id_details(image_path, side="front")
    back_data = extract_id_details(image_path, side="back")

    raw_lines = _get_raw_lines(image_path)

    show_all_results(front_data, back_data, raw_lines, image_path, blur_score)


if __name__ == '__main__':
    main()
