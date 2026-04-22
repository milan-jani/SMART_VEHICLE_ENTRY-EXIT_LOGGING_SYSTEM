import cv2
import os
import sys
import json
import time
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
from app.device.config import DEFAULT_CAMERA_INDEX, AZURE_CV_ENDPOINT, AZURE_CV_KEY


def print_banner():
    """Print a clean startup banner."""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           🪪  ID Card OCR - Smart Scanner  🪪            ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║  Just point your camera at any ID card and press 'c'.   ║")
    print("║  No alignment needed — it reads everything auto!        ║")
    print("║                                                         ║")
    print("║  Controls:                                              ║")
    print("║    'c'  → Capture & Scan                                ║")
    print("║    'q'  → Quit                                          ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def print_separator(char="═", length=58):
    """Print a decorative separator line."""
    print(f"  {char * length}")


def print_section_header(title, icon="📌"):
    """Print a formatted section header."""
    print()
    print_separator()
    print(f"  {icon}  {title}")
    print_separator()


def print_detail(label, value, icon="  "):
    """Print a single detail row with proper formatting."""
    display_val = value if value else "—  (not detected)"
    status = "✅" if value else "❌"
    print(f"  {icon} {status}  {label:<20s}:  {display_val}")


def show_all_results(front_data, back_data, raw_lines_front, raw_lines_back, capture_path):
    """Display all OCR results in a beautiful formatted output."""
    
    print("\n")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║           📋  SCAN RESULTS  📋                       ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    
    # ---------- FRONT SIDE DETAILS ----------
    if front_data:
        if "error" in front_data:
            print_section_header("FRONT SIDE — Error", "⚠️")
            print(f"    {front_data['error']}")
        else:
            print_section_header("FRONT SIDE — Personal Details", "🪪")
            print_detail("Name",       front_data.get("name", ""),      "👤")
            print_detail("ID Number",  front_data.get("id_number", ""), "🔢")
            print_detail("DOB",        front_data.get("dob", ""),       "📅")
            
            conf = front_data.get("confidence", 0)
            conf_bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            print(f"    📊  Confidence          :  [{conf_bar}] {conf*100:.0f}%")
    
    # ---------- BACK SIDE DETAILS ----------
    if back_data:
        if "error" in back_data:
            print_section_header("BACK SIDE — Error", "⚠️")
            print(f"    {back_data['error']}")
        else:
            print_section_header("BACK SIDE — Address Details", "🏠")
            print_detail("Street",  back_data.get("address_street", ""), "📍")
            print_detail("City",    back_data.get("address_city", ""),   "🏙️")
            print_detail("State",   back_data.get("address_state", ""),  "🗺️")
            
            conf = back_data.get("confidence", 0)
            conf_bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
            print(f"    📊  Confidence          :  [{conf_bar}] {conf*100:.0f}%")
    
    # ---------- RAW TEXT ----------
    all_raw = []
    if raw_lines_front:
        all_raw.extend(raw_lines_front)
    if raw_lines_back:
        all_raw.extend(raw_lines_back)
    
    if all_raw:
        print_section_header("RAW OCR TEXT (all lines detected)", "📝")
        for i, line in enumerate(all_raw, 1):
            print(f"    {i:2d}. {line}")
    
    # ---------- SAVED FILE ----------
    print()
    print_separator("─")
    print(f"  💾  Captured image saved: {capture_path}")
    print_separator("─")
    print()


def capture_and_scan(frame, scan_mode="both"):
    """
    Capture the full frame, save it, run OCR, and return results.
    scan_mode: 'front', 'back', or 'both'
    """
    # Save the full frame (no cropping, no ROI)
    os.makedirs("data/temp", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_path = f"data/temp/id_scan_{timestamp}.jpg"
    cv2.imwrite(capture_path, frame)
    
    front_data = None
    back_data = None
    raw_front = None
    raw_back = None
    
    if scan_mode in ("front", "both"):
        print("\n  ⏳  Scanning FRONT side... (sending to Azure OCR)")
        front_data = extract_id_details(capture_path, side="front")
        # Also grab raw lines for display
        raw_front = _get_raw_lines(capture_path)
    
    if scan_mode in ("back", "both"):
        if scan_mode == "both":
            # For "both" mode, back side uses the same image
            # (user flips the card and captures again in separate capture)
            pass
        print("  ⏳  Scanning BACK side... (parsing address from same image)")
        back_data = extract_id_details(capture_path, side="back")
        if not raw_front:
            raw_back = _get_raw_lines(capture_path)
    
    show_all_results(front_data, back_data, raw_front, raw_back, capture_path)
    return front_data, back_data


def _get_raw_lines(image_path):
    """
    Extracts raw text lines from image via Azure OCR (reuses the module logic).
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


def main():
    print_banner()
    
    # Check Azure config
    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        print("  ⚠️  Azure Computer Vision is NOT configured!")
        print("  ➡️  Set AZURE_CV_ENDPOINT and AZURE_CV_KEY in your .env file.")
        print("  ➡️  Without it, OCR will not work.\n")
    else:
        print(f"  ✅  Azure CV configured: {AZURE_CV_ENDPOINT[:40]}...")
        print()

    # Initialize camera
    print("  🎥  Opening camera...")
    cap = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
    
    if not cap.isOpened():
        print("  ❌  Error: Could not open camera. Check camera index in config.py")
        return
    
    print("  ✅  Camera is ready! Show your ID card and press 'c' to scan.\n")
    
    scan_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ❌  Error: Could not read frame from camera.")
            break
        
        # Clean preview — just show the live feed with minimal overlay
        h, w = frame.shape[:2]
        
        # Small info text at the bottom (non-intrusive)
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 40), (w, h), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "Press 'c' to SCAN  |  'q' to QUIT", 
                    (15, h - 12), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Show scan count if any
        if scan_count > 0:
            cv2.putText(frame, f"Scans: {scan_count}", 
                        (w - 120, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
        
        cv2.imshow("ID Scanner - Press 'c' to Scan", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n  👋  Exiting scanner. Goodbye!\n")
            break
        
        elif key == ord('c'):
            scan_count += 1
            print(f"\n  📸  Capture #{scan_count} taken!")
            print("  ─────────────────────────────────────────")
            print("  Which side of the ID card is this?")
            print("    [1] Front  (Name, ID Number, DOB)")
            print("    [2] Back   (Address)")
            print("    [3] Both   (Extract everything from this image)")
            print("  ─────────────────────────────────────────")
            
            # Wait for side selection
            choice = None
            while choice not in ('1', '2', '3'):
                sel_key = cv2.waitKey(0) & 0xFF
                if sel_key == ord('1'):
                    choice = '1'
                elif sel_key == ord('2'):
                    choice = '2'
                elif sel_key == ord('3'):
                    choice = '3'
                elif sel_key == ord('q'):
                    print("\n  👋  Exiting scanner. Goodbye!\n")
                    cap.release()
                    cv2.destroyAllWindows()
                    return
            
            mode_map = {'1': 'front', '2': 'back', '3': 'both'}
            mode_names = {'1': 'FRONT', '2': 'BACK', '3': 'BOTH SIDES'}
            scan_mode = mode_map[choice]
            print(f"  ✔  Scanning: {mode_names[choice]}")
            
            # Read a fresh clean frame (without overlay text)
            ret, clean_frame = cap.read()
            if not ret:
                clean_frame = frame  # fallback
            
            capture_and_scan(clean_frame, scan_mode)
            
            print("  🔄  Ready for next scan! Show another card and press 'c'.\n")
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
