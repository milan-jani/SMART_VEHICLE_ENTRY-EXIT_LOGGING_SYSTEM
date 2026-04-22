import cv2
import os
import sys
import json
import time
import numpy as np
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


# ──────────────────── CONFIGURATION ────────────────────
BLUR_THRESHOLD = 80.0       # Laplacian variance below this = blurry
MAX_CAPTURE_ATTEMPTS = 8    # Max retries to get a sharp frame
CAPTURE_DELAY_MS = 400      # Delay between retries (let user stabilize)
WARMUP_FRAMES = 5           # Frames to skip after 'c' (camera auto-exposure settle)
# ────────────────────────────────────────────────────────


def print_banner():
    """Print a clean startup banner."""
    print()
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           🪪  ID Card OCR — Smart Auto-Scanner  🪪       ║")
    print("╠══════════════════════════════════════════════════════════╣")
    print("║                                                         ║")
    print("║  1. Hold your ID card in front of the camera            ║")
    print("║  2. Press 'c' — system auto-captures a sharp image      ║")
    print("║  3. All details appear automatically!                   ║")
    print("║                                                         ║")
    print("║  ✨ No alignment needed. Blur auto-rejected.            ║")
    print("║                                                         ║")
    print("║  Controls:   'c' = Scan    'q' = Quit                   ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print()


def print_separator(char="═", length=58):
    print(f"  {char * length}")


def print_section_header(title, icon="📌"):
    print()
    print_separator()
    print(f"  {icon}  {title}")
    print_separator()


def print_detail(label, value, icon="  "):
    display_val = value if value else "—  (not detected)"
    status = "✅" if value else "❌"
    print(f"  {icon} {status}  {label:<20s}:  {display_val}")


def calc_blur_score(frame):
    """
    Calculate sharpness/blur score using Laplacian variance.
    Higher = sharper.  Below BLUR_THRESHOLD = blurry.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    return laplacian_var


def smart_capture(cap):
    """
    Smart auto-capture with built-in blur rejection.
    
    Flow:
      1. User presses 'c' — we skip a few warmup frames (auto-exposure settles)
      2. Capture a frame, check blur score
      3. If blurry → discard, show a message on screen, wait a bit, retry
      4. If sharp  → return it
      5. If all attempts blurry → return the sharpest one we got
    """
    
    best_frame = None
    best_score = 0.0
    
    # Skip warmup frames (camera auto-exposure / auto-focus settle)
    print("  ⏳  Focusing...")
    for _ in range(WARMUP_FRAMES):
        cap.read()
        cv2.waitKey(50)
    
    for attempt in range(1, MAX_CAPTURE_ATTEMPTS + 1):
        ret, frame = cap.read()
        if not ret:
            continue
        
        score = calc_blur_score(frame)
        
        # Track the best (sharpest) frame we've seen
        if score > best_score:
            best_score = score
            best_frame = frame.copy()
        
        if score >= BLUR_THRESHOLD:
            # Sharp enough — use it!
            print(f"  ✅  Attempt {attempt}: Sharp! (score: {score:.1f})")
            return frame, score
        else:
            # Blurry — show feedback and retry
            print(f"  🔄  Attempt {attempt}: Blurry (score: {score:.1f}) — hold steady, retrying...")
            
            # Show "Hold steady..." message on the preview
            display = frame.copy()
            h, w = display.shape[:2]
            overlay = display.copy()
            cv2.rectangle(overlay, (0, 0), (w, 50), (0, 0, 200), -1)
            cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
            cv2.putText(display, f"Blurry! Hold steady... (attempt {attempt}/{MAX_CAPTURE_ATTEMPTS})",
                        (15, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
            cv2.imshow("ID Scanner - Press 'c' to Scan", display)
            cv2.waitKey(CAPTURE_DELAY_MS)
    
    # All attempts were blurry — return the best one we got
    if best_frame is not None:
        print(f"  ⚠️  Could not get a perfectly sharp frame. Using best (score: {best_score:.1f})")
        return best_frame, best_score
    
    return None, 0.0


def show_all_results(front_data, back_data, raw_lines, capture_path, blur_score):
    """Display all OCR results in a beautiful formatted output."""
    
    print("\n")
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║           📋  SCAN RESULTS  📋                       ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    
    # ---------- Image Quality ----------
    quality = "Excellent" if blur_score > 200 else "Good" if blur_score > BLUR_THRESHOLD else "Fair (may affect accuracy)"
    quality_icon = "🟢" if blur_score > 200 else "🟡" if blur_score > BLUR_THRESHOLD else "🔴"
    print(f"\n  {quality_icon}  Image Quality: {quality} (sharpness: {blur_score:.0f})")
    
    # ---------- FRONT SIDE DETAILS ----------
    if front_data:
        if "error" in front_data:
            print_section_header("FRONT SIDE — Error", "⚠️")
            print(f"    {front_data['error']}")
        else:
            print_section_header("PERSONAL DETAILS (Front Side)", "🪪")
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
            has_address = any([
                back_data.get("address_street"),
                back_data.get("address_city"),
                back_data.get("address_state")
            ])
            if has_address:
                print_section_header("ADDRESS DETAILS (Back Side)", "🏠")
                print_detail("Street",  back_data.get("address_street", ""), "📍")
                print_detail("City",    back_data.get("address_city", ""),   "🏙️")
                print_detail("State",   back_data.get("address_state", ""),  "🗺️")
                
                conf = back_data.get("confidence", 0)
                conf_bar = "█" * int(conf * 20) + "░" * (20 - int(conf * 20))
                print(f"    📊  Confidence          :  [{conf_bar}] {conf*100:.0f}%")
    
    # ---------- RAW TEXT ----------
    if raw_lines:
        print_section_header("RAW OCR TEXT (all lines detected)", "📝")
        for i, line in enumerate(raw_lines, 1):
            print(f"    {i:2d}. {line}")
    
    # ---------- SAVED FILE ----------
    print()
    print_separator("─")
    print(f"  💾  Captured image saved: {capture_path}")
    print_separator("─")
    print()


def capture_and_scan(cap):
    """
    One-button smart capture + OCR.
    Auto-rejects blur, retries until sharp, then scans both sides.
    """
    # Smart capture with blur rejection
    frame, blur_score = smart_capture(cap)
    
    if frame is None:
        print("  ❌  Failed to capture any frame.")
        return
    
    # Save the captured frame
    os.makedirs("data/temp", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    capture_path = f"data/temp/id_scan_{timestamp}.jpg"
    cv2.imwrite(capture_path, frame)
    
    # Show a "Processing..." flash on the camera preview
    display = frame.copy()
    h, w = display.shape[:2]
    overlay = display.copy()
    cv2.rectangle(overlay, (0, 0), (w, 50), (0, 150, 0), -1)
    cv2.addWeighted(overlay, 0.7, display, 0.3, 0, display)
    cv2.putText(display, "Captured! Processing OCR...",
                (15, 33), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.imshow("ID Scanner - Press 'c' to Scan", display)
    cv2.waitKey(100)
    
    # Run BOTH front and back OCR on the same image
    # This way user gets ALL possible details from whatever side they show
    print("\n  ⏳  Running OCR (extracting all details)...")
    
    front_data = extract_id_details(capture_path, side="front")
    back_data = extract_id_details(capture_path, side="back")
    
    # Get raw lines for display
    raw_lines = _get_raw_lines(capture_path)
    
    # Show everything
    show_all_results(front_data, back_data, raw_lines, capture_path, blur_score)


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


def main():
    print_banner()
    
    # Check Azure config
    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        print("  ⚠️   Azure Computer Vision is NOT configured!")
        print("  ➡️   Set AZURE_CV_ENDPOINT and AZURE_CV_KEY in your .env file.")
        print("  ➡️   Without it, OCR will not work.\n")
    else:
        print(f"  ✅  Azure CV connected: {AZURE_CV_ENDPOINT[:40]}...")
        print()

    # Initialize camera
    print("  🎥  Opening camera...")
    cap = cv2.VideoCapture(DEFAULT_CAMERA_INDEX)
    
    if not cap.isOpened():
        print("  ❌  Error: Could not open camera. Check camera index in config.py")
        return
    
    # Let camera warm up
    for _ in range(10):
        cap.read()
    
    print("  ✅  Camera ready!")
    print("  ➡️  Hold your ID card in front and press 'c'. That's it!\n")
    
    scan_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("  ❌  Error: Could not read frame from camera.")
            break
        
        h, w = frame.shape[:2]
        
        # Live blur score indicator (small, non-intrusive)
        live_score = calc_blur_score(frame)
        score_color = (0, 255, 0) if live_score >= BLUR_THRESHOLD else (0, 165, 255)
        score_label = "Sharp" if live_score >= BLUR_THRESHOLD else "Move closer / hold steady"
        
        # Bottom bar overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, h - 45), (w, h), (30, 30, 30), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)
        
        cv2.putText(frame, "Press 'c' to SCAN  |  'q' to QUIT",
                    (15, h - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        
        # Sharpness indicator (top-right)
        indicator_w = min(int(live_score / 3), 150)
        cv2.rectangle(frame, (w - 170, 10), (w - 170 + indicator_w, 25), score_color, -1)
        cv2.rectangle(frame, (w - 170, 10), (w - 20, 25), (100, 100, 100), 1)
        cv2.putText(frame, score_label, (w - 170, 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, score_color, 1, cv2.LINE_AA)
        
        # Scan count badge
        if scan_count > 0:
            cv2.putText(frame, f"Scans: {scan_count}",
                        (15, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 1, cv2.LINE_AA)
        
        cv2.imshow("ID Scanner - Press 'c' to Scan", frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            print("\n  👋  Exiting scanner. Goodbye!\n")
            break
        
        elif key == ord('c'):
            scan_count += 1
            print(f"\n  📸  Scan #{scan_count} started — auto-capturing best frame...")
            capture_and_scan(cap)
            print("  🔄  Ready! Show another card and press 'c' again.\n")
    
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
