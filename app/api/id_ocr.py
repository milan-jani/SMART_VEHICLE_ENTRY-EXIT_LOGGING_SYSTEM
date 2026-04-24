"""
Azure Computer Vision OCR Module
Extracts details from ID cards (Aadhaar, PAN, DL) using Azure Computer Vision v3.2.
Supports: Aadhaar Card, Driving License (DL), PAN Card, Voter ID

Uses unified label-aware parsing and spatial filtering to ignore right-side noise.
"""
import os
import time
import requests
import re

from app.device.config import AZURE_CV_ENDPOINT, AZURE_CV_KEY


def extract_id_details(image_path: str, side: str = "front") -> dict:
    """
    Sends the image to Azure Computer Vision Read API and extracts text details.
    Uses spatial filtering to ignore noise on the right side of the card.
    """
    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        return {"error": "Azure Computer Vision not configured"}
        
    full_image_path = os.path.abspath(image_path)
    if not os.path.exists(full_image_path):
        return {"error": f"Image file not found: {image_path}"}
        
    # Azure v3.2 Read endpoint
    analyze_url = f"{AZURE_CV_ENDPOINT.rstrip('/')}/vision/v3.2/read/analyze"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_CV_KEY,
        'Content-Type': 'application/octet-stream'
    }
    
    try:
        # Step 1: Submit image to Azure
        with open(full_image_path, "rb") as image_data:
            response = requests.post(analyze_url, headers=headers, data=image_data)
            
        if response.status_code not in [200, 202]:
            print(f"[ERROR] Azure OCR API Error: {response.status_code} - {response.text}")
            return {"error": f"Azure API Error: {response.text}"}
            
        operation_url = response.headers.get("Operation-Location")
        if not operation_url:
            return {"error": "No operation location received from Azure"}
            
        # Step 2: Poll for results
        poll_headers = {'Ocp-Apim-Subscription-Key': AZURE_CV_KEY}
        max_retries = 15
        ocr_result = None
        
        for _ in range(max_retries):
            time.sleep(1.0)
            poll_resp = requests.get(operation_url, headers=poll_headers)
            poll_resp.raise_for_status()
            
            result_json = poll_resp.json()
            if result_json.get("status") == "succeeded":
                ocr_result = result_json
                break
            elif result_json.get("status") == "failed":
                return {"error": "Azure OCR processing failed"}
                
        if not ocr_result:
            return {"error": "OCR polling timed out"}
            
        # Step 3: Extract lines with spatial info
        lines = []
        read_results = ocr_result.get("analyzeResult", {}).get("readResults", [])
        if not read_results:
            return {"error": "No text detected in image"}
            
        page = read_results[0]
        img_width = page.get("width", 1)
        
        for line_obj in page.get("lines", []):
            text = line_obj.get("text", "").strip()
            bbox = line_obj.get("boundingBox", [0]*8)
            # min_x is the left-most position
            min_x = min(bbox[0], bbox[2], bbox[4], bbox[6])
            lines.append({
                "text": text,
                "x": min_x
            })
                
        if not lines:
            return {"error": "No text detected in image"}
        
        # Debug: log raw OCR lines in terminal
        print(f"[OCR] Raw lines detected ({len(lines)}):")
        for i, line in enumerate(lines):
            print(f"  {i+1}. [{int(line['x'])}] {line['text']}")
            
        # Detect document type
        doc_type = _detect_document_type(lines)
        print(f"[OCR] Detected document type: {doc_type}")
        
        # Extract all fields using spatial context and side awareness
        result = _extract_all_fields(lines, doc_type, img_width, side)
        
        print(f"[OCR] Extracted ({side}): name='{result.get('name')}', id='{result.get('id_number')}', "
              f"dob='{result.get('dob')}', address='{result.get('address')}'")
        
        return result
            
    except Exception as e:
        print(f"[ERROR] OCR extraction error: {str(e)}")
        return {"error": f"OCR extraction error: {str(e)}"}


# ─────────────────────────────────────────────────────────────
#  Document Type Detection
# ─────────────────────────────────────────────────────────────

def _detect_document_type(lines):
    """Detect if the document is Aadhaar, DL, PAN, Voter ID, etc."""
    full_text = " ".join([l['text'] for l in lines]).upper()
    
    if "DRIVING" in full_text and ("LICENCE" in full_text or "LICENSE" in full_text):
        return "DL"
    if any(w in full_text for w in ["AADHAAR", "UIDAI", "UNIQUE IDENTIFICATION"]):
        return "AADHAAR"
    if any(w in full_text for w in ["INCOME TAX", "PERMANENT ACCOUNT"]):
        return "PAN"
    if any(w in full_text for w in ["ELECTION", "VOTER", "NIRVACHAN"]):
        return "VOTER"
    
    # Detect by ID number patterns if header text not found
    for line in lines:
        text = line['text'].upper()
        if re.search(r'\b[A-Z]{2}\d{2}\s?\d{11,13}\b', text):
            return "DL"
        if re.search(r'\b\d{4}\s\d{4}\s\d{4}\b', text):
            return "AADHAAR"
        if re.search(r'\b[A-Z]{5}\d{4}[A-Z]\b', text):
            return "PAN"
    
    return "UNKNOWN"


# ─────────────────────────────────────────────────────────────
#  Universal Field Extractor
# ─────────────────────────────────────────────────────────────

def _extract_all_fields(lines, doc_type, img_width, side="front"):
    """
    Universal field extractor for Indian ID documents.
    """
    # 1. DISABLE DL BACK SIDE: Per user request, DL back side has no useful info and causes noise.
    if doc_type == "DL" and side == "back":
        print("[OCR] DL Back side detected. Skipping extraction as requested.")
        return {
            "name": "", "id_number": "", "dob": "", "phone": "", "address": "",
            "message": "Back side not required for DL",
            "confidence": 1.0
        }

    result = {
        "name": "",
        "id_number": "",
        "dob": "",
        "phone": "",
        "address": "",
        "confidence": 0.85
    }
    
    # Only extract identity info from the front side
    if side == "front":
        _extract_id_number(lines, result)
        _extract_name(lines, result, doc_type)
        _extract_dob(lines, result, doc_type)
    
    # Always try to extract address (can be on either side, but mostly back)
    _extract_address_and_phone(lines, result, doc_type, img_width)
    
    return result


def _extract_id_number(lines, result):
    """Extract ID number (DL, Aadhaar, PAN, Voter ID)."""
    for line in lines:
        if result["id_number"]:
            break
        text = line['text'].upper().strip()
        
        # DL number: GJ25 20230003704
        m = re.search(r'\b([A-Z]{2}\d{2}\s?\d{11,13})\b', text)
        if m:
            result["id_number"] = m.group(1)
            continue
        
        # Aadhaar
        if "VID" not in text:
            m = re.search(r'\b(\d{4}\s\d{4}\s\d{4})\b', text)
            if m:
                result["id_number"] = m.group(1)
                continue
        
        # PAN: ABCDE1234F
        m = re.search(r'\b([A-Z]{5}\d{4}[A-Z])\b', text)
        if m:
            result["id_number"] = m.group(1)
            continue


def _extract_name(lines, result, doc_type):
    """Extract person's name — label-based first, then heuristic fallback."""
    
    for line in lines:
        upper = line['text'].upper().strip()
        
        m = re.match(r'NAME\s*[:：]?\s+(.+)', upper)
        if m:
            name_val = m.group(1).strip()
            # Clean noise
            name_val = re.sub(r"HOLDER.*", "", name_val, flags=re.IGNORECASE).strip()
            name_val = re.sub(r"[^A-Za-z\s]", "", name_val).strip()
            if len(name_val) > 2:
                result["name"] = name_val.title()
            return
    
    # Heuristic fallback
    SKIP_WORDS = {
        "GOVERNMENT", "INDIA", "AADHAAR", "MALE", "FEMALE", "DOB", "VID",
        "ISSUE", "DRIVING", "LICENCE", "LICENSE", "UNION", "UNIQUE",
        "IDENTIFICATION", "AUTHORITY", "ELECTION", "COMMISSION",
        "HOLDER", "SIGNATURE", "BLOOD", "GROUP", "ORGAN", "DONOR",
        "SON", "DAUGHTER", "WIFE", "VALIDITY", "INCOME", "TAX",
        "DEPARTMENT", "PERMANENT", "ACCOUNT", "ADDRESS", "ADD",
        "TRANSPORT", "STATE", "DATE", "BIRTH", "FATHER", "HUSBAND"
    }
    
    for line in lines:
        text = line['text'].strip()
        upper = text.upper()
        
        if any(w in upper for w in SKIP_WORDS): continue
        if any(ord(c) > 127 for c in text): continue
        if re.search(r'\d', text): continue
        if len(text) <= 4: continue
        
        if re.match(r'^[A-Za-z][A-Za-z\s]+$', text) and len(text.split()) >= 2:
            result["name"] = text.title()
            return


def _extract_dob(lines, result, doc_type):
    """Extract Date of Birth."""
    for line in lines:
        upper = line['text'].upper().strip()
        m = re.search(
            r'(?:D\.?O\.?B\.?|DATE\s*OF\s*BIRTH)\s*[:：]\s*(\d{2}[-/]\d{2}[-/]\d{4})',
            upper
        )
        if m:
            result["dob"] = _format_date(m.group(1))
            return
    
    # Fallback to first date found that is not issue/validity
    for line in lines:
        upper = line['text'].upper()
        if any(w in upper for w in ["ISSUE", "VALID", "EXPIR"]): continue
        m = re.search(r'\b(\d{2}[-/]\d{2}[-/]\d{4})\b', upper)
        if m:
            result["dob"] = _format_date(m.group(1))
            return


def _extract_address_and_phone(lines, result, doc_type, img_width):
    """
    Extract address and phone. 
    Uses img_width and line['x'] to filter out right-side metadata (Issue dates, etc.)
    """
    address_lines = []
    capturing = False
    
    # Noise text that often appears on DL right-side
    RIGHT_SIDE_NOISE = r'\b(HOLDER|SIGNATURE|ORGAN\s*DONOR|BLOOD\s*GROUP|DATE\s*OF\s*FIRST\s*ISSUE|AUTHORITY|REGISTERING)\b'
    
    # Max X allowed for address lines (address is usually on the left/center)
    # 75% of image width is a safe threshold for most DLs
    MAX_ADDRESS_X = img_width * 0.75
    
    for line in lines:
        text = line['text'].strip()
        upper = text.upper()
        lx = line['x']
        
        # 1. Detect address start
        if re.search(r'\bADDRESS\b', upper) or re.search(r'\bADD\s*:', upper):
            capturing = True
            after = re.split(r'(?:ADDRESS|ADD)\s*[:：]?\s*', upper, maxsplit=1)
            if len(after) > 1 and len(after[-1].strip()) > 2:
                # Still check spatial for the inline content
                if lx < MAX_ADDRESS_X:
                    address_lines.append(after[-1].strip().title())
            continue
        
        if capturing:
            # SPATIAL FILTER: Ignore lines on the extreme right
            if lx > MAX_ADDRESS_X:
                print(f"[OCR] Skipping right-side noise (spatial): {text}")
                continue
                
            # TEXT FILTER: Ignore common noise labels
            if re.search(RIGHT_SIDE_NOISE, upper):
                continue
            
            # Stop markers
            if re.search(r'\b(VID|DOWNLOAD|HELP|WWW\.|1947|ISSUE\s*DATE|NAME\s*:)\b', upper):
                # Don't stop immediately if it's just one line of noise, 
                # but if it looks like a new section, stop.
                if "NAME" in upper or "ISSUE" in upper:
                    capturing = False
                continue
            
            # Skip non-ASCII
            if any(ord(c) > 127 for c in text): continue
            
            # Clean artifacts
            if (len(text) <= 2 and not any(c.isdigit() for c in text)) or upper in ['DAT', 'DAT,']:
                continue
            
            address_lines.append(text.title())
            
            # Pincode usually ends address
            if re.search(r'\b\d{6}\b', text):
                capturing = False
    
    # Fallback for DL address
    if not address_lines and doc_type == "DL":
        for i, line in enumerate(lines):
            upper = line['text'].upper()
            lx = line['x']
            if lx < MAX_ADDRESS_X and re.search(r'\b(FLAT\s*N|HOUSE\s*N|ROOM\s*N|PLOT|BLOCK|BLDG|STREET|ROAD|LANE|NAGAR|COLONY|SECTOR|VILLAGE|DIST)\b', upper):
                for j in range(i, min(i + 5, len(lines))):
                    l_obj = lines[j]
                    t, x = l_obj['text'], l_obj['x']
                    if x > MAX_ADDRESS_X: continue
                    if re.search(RIGHT_SIDE_NOISE, t.upper()): continue
                    if any(ord(c) > 127 for c in t): continue
                    if len(t) < 3: continue
                    address_lines.append(t.title())
                    if re.search(r'\b\d{6}\b', t): break
                break
    
    # Phone extraction
    cleaned = []
    for al in address_lines:
        m = re.search(r'MOB(?:ILE)?\s*(?:NO|NUMBER|\.?)\s*[:.]?\s*(\d{10})', al, re.IGNORECASE)
        if m:
            result["phone"] = m.group(1)
            al = re.sub(r',?\s*MOB(?:ILE)?\s*(?:NO|NUMBER|\.?)\s*[:.]?\s*\d{10}', '', al, flags=re.IGNORECASE).strip()
        
        if not result["phone"]:
            m2 = re.search(r',\s*(\d{10})\b', al)
            if m2:
                result["phone"] = m2.group(1)
                al = re.sub(r',\s*\d{10}\b', '', al).strip()
        
        al = al.rstrip(',').strip()
        if al: cleaned.append(al)
    
    if cleaned:
        result["address"] = ", ".join(cleaned).strip().rstrip(',').strip()


def _format_date(date_str):
    """Convert DD/MM/YYYY to YYYY-MM-DD."""
    d_str = date_str.replace("/", "-")
    parts = d_str.split("-")
    if len(parts) == 3 and len(parts[2]) == 4:
        return f"{parts[2]}-{parts[1]}-{parts[0]}"
    return d_str
